from app import db
from datetime import datetime
import json
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Task metadata
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, archived
    priority = db.Column(db.Integer, default=0)  # 0-5 scale
    estimated_duration = db.Column(db.Integer)  # in minutes
    actual_duration = db.Column(db.Integer)  # in minutes
    
    # AI-generated fields
    category = db.Column(db.String(50))
    complexity_score = db.Column(db.Float)
    sentiment_score = db.Column(db.Float)
    keywords = db.Column(db.JSON)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    subtasks = relationship('Task', backref=db.backref('parent', remote_side=[id]))
    
    # Dependencies
    dependencies = db.relationship(
        'TaskDependency',
        primaryjoin='Task.id==TaskDependency.task_id',
        backref='task',
        lazy='dynamic'
    )
    
    # Tags and labels
    tags = db.Column(db.JSON)
    
    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)
        self.tags = json.dumps([]) if not self.tags else self.tags
    
    @hybrid_property
    def is_completed(self):
        return self.status == 'completed'
    
    @hybrid_property
    def is_overdue(self):
        return self.due_date and self.due_date < datetime.utcnow() and not self.is_completed
    
    def add_dependency(self, dependent_task):
        """Add a dependency to this task"""
        if dependent_task.id == self.id:
            raise ValueError("A task cannot depend on itself")
        dependency = TaskDependency(task_id=self.id, dependent_task_id=dependent_task.id)
        db.session.add(dependency)
    
    def remove_dependency(self, dependent_task):
        """Remove a dependency from this task"""
        TaskDependency.query.filter_by(
            task_id=self.id,
            dependent_task_id=dependent_task.id
        ).delete()
    
    def get_dependent_tasks(self):
        """Get all tasks that depend on this task"""
        return Task.query.join(TaskDependency).filter(
            TaskDependency.dependent_task_id == self.id
        ).all()
    
    def calculate_priority_score(self):
        """Calculate a priority score based on various factors"""
        score = 0
        
        # Due date factor
        if self.due_date:
            days_until_due = (self.due_date - datetime.utcnow()).days
            if days_until_due < 0:
                score += 5  # Overdue tasks get highest priority
            elif days_until_due < 1:
                score += 4
            elif days_until_due < 3:
                score += 3
            elif days_until_due < 7:
                score += 2
            else:
                score += 1
        
        # Complexity factor
        if self.complexity_score:
            score += self.complexity_score * 2
        
        # Dependencies factor
        dependency_count = self.dependencies.count()
        score += min(dependency_count, 3)  # Cap at 3 points
        
        return min(score, 5)  # Cap at 5
    
    def to_dict(self):
        """Convert task to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'category': self.category,
            'complexity_score': self.complexity_score,
            'tags': json.loads(self.tags) if isinstance(self.tags, str) else self.tags,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'is_completed': self.is_completed,
            'is_overdue': self.is_overdue
        }

class TaskDependency(db.Model):
    __tablename__ = 'task_dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    dependent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'dependent_task_id', name='unique_task_dependency'),
    ) 