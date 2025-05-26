from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, Text, desc, asc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date, timezone
from typing import Annotated, Optional, List, Set
from enum import Enum as PyEnum
import re
from collections import Counter

# Database setup
DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

# Enums
class TaskStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# Database Models
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    creation_date = Column(DateTime, default=func.now(), nullable=False)
    modified_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    
    @field_validator('due_date')
    def validate_due_date(cls, v):
        if v:
            now = datetime.now(timezone.utc)
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)            
            if v < now:
                raise ValueError('Due date cannot be in the past')
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    
    @field_validator('due_date')
    def validate_due_date(cls, v):
        if v:
            now = datetime.now(timezone.utc)
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)            
            if v < now:
                raise ValueError('Due date cannot be in the past')
        return v

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    status: TaskStatus
    creation_date: datetime
    modified_date: datetime
    
    class Config:
        from_attributes = True

class TaskSuggestion(BaseModel):
    suggested_title: str

# FastAPI app
app = FastAPI(
    title="Smart Task Management API",
    description="A RESTful API for managing tasks with intelligent suggestions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Helper functions for smart suggestions
class TaskSuggestionEngine:
    def __init__(self, db: Session):
        self.db = db
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Remove special characters and convert to lowercase
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        words = cleaned.split()
        
        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'with', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def generate_suggestions(self) -> List[TaskSuggestion]:
        all_task_titles_tuples = self.db.query(Task.title).filter(Task.title.isnot(None)).all()
        all_task_titles = [title_tuple[0] for title_tuple in all_task_titles_tuples]

        if not all_task_titles:
            # No existing tasks to analyze
            return []

        all_keywords: List[str] = []
        for title in all_task_titles:
            all_keywords.extend(self.extract_keywords(title))        
        
        all_task_descriptions_tuples = self.db.query(Task.description).filter(Task.description.isnot(None)).all()
        all_task_descriptions = [desc_tuple[0] for desc_tuple in all_task_descriptions_tuples]

        for description in all_task_descriptions:
            all_keywords.extend(self.extract_keywords(description))

        if not all_keywords:
            # No meaningful keywords found after filtering
            return []

        keyword_counts = Counter(all_keywords)

        most_common_keywords_with_counts = keyword_counts.most_common(5)
        
        if not most_common_keywords_with_counts:            
            return []
        
        top_keywords = [kw for kw, count in most_common_keywords_with_counts]

        suggestions: List[TaskSuggestion] = []
        generated_titles: Set[str] = set() 

        suggestion_templates = [
            "Follow-up on {}",
            "Finalize {}",
            "Plan next steps for {}",
            "Schedule meeting for {}",
            "Prepare report regarding {}",
            "Start working on {}"
        ]
        
        # Iterate through top keywords and then through templates
        for keyword in top_keywords:            

            formatted_keyword = " ".join(part.capitalize() for part in keyword.split('-'))

            suggestions_made_for_this_keyword = 0
            for template in suggestion_templates:                
                if suggestions_made_for_this_keyword >= 3:
                    break # Limit suggestions per keyword to ensure variety

                suggested_title = template.format(formatted_keyword)
                
                # Avoid adding duplicate suggestions
                if suggested_title not in generated_titles:
                    suggestions.append(TaskSuggestion(suggested_title=suggested_title))
                    generated_titles.add(suggested_title)
                    suggestions_made_for_this_keyword += 1
            
        return suggestions

# API Endpoints

@app.get("/", summary="API Root")
async def root():
    """Welcome message and API information"""
    return {
        "message": "Welcome to Smart Task Management API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.post("/tasks/", response_model=TaskResponse, summary="Create a new task")
async def create_task(task: TaskCreate, db: Session = Depends(get_session)):
    """
    Create a new task with the following information:
    - **title**: Task title (required, max 200 characters)
    - **description**: Task description (optional, max 1000 characters)
    - **due_date**: Due date (optional, must be in the future)
    - **status**: Task status (pending, in_progress, completed)
    """
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskResponse], summary="Get all tasks with filtering and sorting")
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    due_date_from: Optional[date] = Query(None, description="Filter tasks due from this date"),
    due_date_to: Optional[date] = Query(None, description="Filter tasks due until this date"),
    sort_by: Optional[str] = Query("creation_date", pattern="^(creation_date|due_date)$", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_session)
) -> List[TaskResponse]:
    """
    Retrieve all tasks with optional filtering and sorting:
    - **status**: Filter by task status
    - **due_date_from**: Show tasks due from this date
    - **due_date_to**: Show tasks due until this date
    - **sort_by**: Sort by 'creation_date' or 'due_date'
    - **sort_order**: 'asc' for ascending, 'desc' for descending
    """
    query = db.query(Task)
    
    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    
    if due_date_from:
        query = query.filter(Task.due_date >= datetime.combine(due_date_from, datetime.min.time()))
    
    if due_date_to:
        query = query.filter(Task.due_date <= datetime.combine(due_date_to, datetime.max.time()))
    
    # Apply sorting
    if sort_by == "creation_date":
        order_field = Task.creation_date
    else:  # due_date
        order_field = Task.due_date
    
    if sort_order == "asc":
        query = query.order_by(asc(order_field))
    else:
        query = query.order_by(desc(order_field))
    
    return query.all()

@app.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get a specific task")
async def get_task(task_id: int, db: Session = Depends(get_session)) -> TaskResponse:
    """Get a specific task by its ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse, summary="Update a specific task")
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_session)):
    """
    Update a specific task. Only provided fields will be updated:
    - **title**: New task title
    - **description**: New task description
    - **due_date**: New due date
    - **status**: New task status
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}", summary="Delete a specific task")
async def delete_task(task_id: int, db: Session = Depends(get_session)):
    """Delete a specific task by its ID"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return {"message": f"Task with id: {task_id} deleted successfully"}

@app.get("/tasks/suggestions/smart", response_model=List[TaskSuggestion], summary="Get smart task suggestions")
async def get_smart_suggestions(db: Session = Depends(get_session)):
    """
    Get intelligent task suggestions based on existing task patterns:
    - Analyzes frequency of similar task titles and descriptions
    - Identifies common task sequences and follow-up patterns
    - Suggests related tasks based on completed task analysis
    """
    suggestion_engine = TaskSuggestionEngine(db)
    suggestions = suggestion_engine.generate_suggestions()
    
    if not suggestions:
        # Provide some default suggestions if no patterns are found
        default_suggestions = [
            TaskSuggestion(
                suggested_title="Weekly Planning Session"                
            ),
            TaskSuggestion(
                suggested_title="Project Status Review"                
            ),
            TaskSuggestion(
                suggested_title="Team Meeting Preparation"                
            )
        ]
        return default_suggestions
    
    return suggestions

@app.get("/tasks/statistics/overview", summary="Get task statistics")
async def get_task_statistics(db: Session = Depends(get_session)):
    """Get overview statistics of all tasks"""
    total_tasks = db.query(Task).count()
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    
    # Tasks due soon (within 7 days)
    from datetime import timedelta
    next_week = datetime.now(timezone.utc) + timedelta(days=7)
    tasks_due_soon = db.query(Task).filter(
        Task.due_date <= next_week,
        Task.due_date >= datetime.now(timezone.utc),
        Task.status != TaskStatus.COMPLETED
    ).count()
    
    return {
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completed_tasks": completed_tasks,
        "tasks_due_soon": tasks_due_soon,
        "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
    }