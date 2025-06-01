from app import db
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.hybrid import hybrid_property

class UserAnalytics(db.Model):
    __tablename__ = 'user_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Productivity metrics
    total_tasks_completed = db.Column(db.Integer, default=0)
    total_tasks_created = db.Column(db.Integer, default=0)
    average_completion_time = db.Column(db.Float)  # in minutes
    completion_rate = db.Column(db.Float)  # percentage
    
    # Time tracking
    total_productive_time = db.Column(db.Integer, default=0)  # in minutes
    average_daily_productive_time = db.Column(db.Float)  # in minutes
    most_productive_hours = db.Column(db.JSON)
    
    # Task patterns
    common_categories = db.Column(db.JSON)
    common_tags = db.Column(db.JSON)
    task_complexity_distribution = db.Column(db.JSON)
    
    # Streak tracking
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(UserAnalytics, self).__init__(**kwargs)
        self.most_productive_hours = json.dumps({})
        self.common_categories = json.dumps({})
        self.common_tags = json.dumps({})
        self.task_complexity_distribution = json.dumps({})
    
    def update_completion_metrics(self, task):
        """Update metrics when a task is completed"""
        self.total_tasks_completed += 1
        
        # Update completion time
        if task.actual_duration:
            if self.average_completion_time is None:
                self.average_completion_time = task.actual_duration
            else:
                self.average_completion_time = (
                    (self.average_completion_time * (self.total_tasks_completed - 1) +
                     task.actual_duration) / self.total_tasks_completed
                )
        
        # Update completion rate
        self.completion_rate = (self.total_tasks_completed / self.total_tasks_created * 100
                              if self.total_tasks_created > 0 else 0)
        
        # Update productive time
        if task.actual_duration:
            self.total_productive_time += task.actual_duration
        
        # Update streaks
        self._update_streak()
        
        # Update category and tag statistics
        self._update_category_stats(task.category)
        if task.tags:
            for tag in json.loads(task.tags) if isinstance(task.tags, str) else task.tags:
                self._update_tag_stats(tag)
        
        # Update complexity distribution
        if task.complexity_score:
            self._update_complexity_distribution(task.complexity_score)
    
    def _update_streak(self):
        """Update user's activity streak"""
        today = datetime.utcnow().date()
        
        if not self.last_activity_date:
            self.current_streak = 1
        else:
            last_activity = self.last_activity_date.date()
            if today - last_activity == timedelta(days=1):
                self.current_streak += 1
            elif today - last_activity > timedelta(days=1):
                self.current_streak = 1
        
        self.last_activity_date = datetime.utcnow()
        self.longest_streak = max(self.longest_streak, self.current_streak)
    
    def _update_category_stats(self, category):
        """Update statistics for task categories"""
        if not category:
            return
        
        categories = json.loads(self.common_categories) if isinstance(self.common_categories, str) else self.common_categories
        categories[category] = categories.get(category, 0) + 1
        self.common_categories = json.dumps(categories)
    
    def _update_tag_stats(self, tag):
        """Update statistics for task tags"""
        tags = json.loads(self.common_tags) if isinstance(self.common_tags, str) else self.common_tags
        tags[tag] = tags.get(tag, 0) + 1
        self.common_tags = json.dumps(tags)
    
    def _update_complexity_distribution(self, complexity_score):
        """Update distribution of task complexity scores"""
        distribution = json.loads(self.task_complexity_distribution) if isinstance(self.task_complexity_distribution, str) else self.task_complexity_distribution
        
        # Round complexity score to nearest 0.5
        rounded_score = round(complexity_score * 2) / 2
        distribution[str(rounded_score)] = distribution.get(str(rounded_score), 0) + 1
        
        self.task_complexity_distribution = json.dumps(distribution)
    
    def calculate_productivity_score(self):
        """Calculate overall productivity score (0-100)"""
        if self.total_tasks_created == 0:
            return 0
        
        # Factors that contribute to productivity score
        completion_rate_weight = 0.4
        streak_weight = 0.2
        time_efficiency_weight = 0.2
        consistency_weight = 0.2
        
        # Completion rate factor (0-100)
        completion_rate_score = self.completion_rate
        
        # Streak factor (0-100)
        streak_score = min(self.current_streak * 10, 100)
        
        # Time efficiency factor (0-100)
        time_efficiency_score = 0
        if self.average_completion_time and self.average_daily_productive_time:
            # Calculate how well the user estimates task duration
            time_efficiency_score = min(
                (self.average_daily_productive_time / self.average_completion_time) * 50,
                100
            )
        
        # Consistency factor (0-100)
        consistency_score = 0
        if self.most_productive_hours:
            hours = json.loads(self.most_productive_hours) if isinstance(self.most_productive_hours, str) else self.most_productive_hours
            if hours:
                # Calculate how consistent the user's productive hours are
                max_hours = max(hours.values())
                total_hours = sum(hours.values())
                consistency_score = (max_hours / total_hours) * 100
        
        # Calculate final score
        final_score = (
            completion_rate_score * completion_rate_weight +
            streak_score * streak_weight +
            time_efficiency_score * time_efficiency_weight +
            consistency_score * consistency_weight
        )
        
        return round(final_score, 2)
    
    def to_dict(self):
        """Convert analytics to dictionary for API responses"""
        return {
            'total_tasks_completed': self.total_tasks_completed,
            'total_tasks_created': self.total_tasks_created,
            'completion_rate': self.completion_rate,
            'average_completion_time': self.average_completion_time,
            'total_productive_time': self.total_productive_time,
            'average_daily_productive_time': self.average_daily_productive_time,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'productivity_score': self.calculate_productivity_score(),
            'most_productive_hours': json.loads(self.most_productive_hours) if isinstance(self.most_productive_hours, str) else self.most_productive_hours,
            'common_categories': json.loads(self.common_categories) if isinstance(self.common_categories, str) else self.common_categories,
            'common_tags': json.loads(self.common_tags) if isinstance(self.common_tags, str) else self.common_tags,
            'task_complexity_distribution': json.loads(self.task_complexity_distribution) if isinstance(self.task_complexity_distribution, str) else self.task_complexity_distribution
        } 