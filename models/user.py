from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import bcrypt
from sqlalchemy.ext.hybrid import hybrid_property

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Profile information
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    timezone = db.Column(db.String(50))
    preferred_working_hours = db.Column(db.JSON)
    
    # Relationships
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    analytics = db.relationship('UserAnalytics', backref='user', uselist=False)
    
    @hybrid_property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        salt = bcrypt.gensalt()
        self._password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self._password_hash.encode('utf-8'))
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def get_task_completion_rate(self):
        completed = self.tasks.filter_by(status='completed').count()
        total = self.tasks.count()
        return (completed / total * 100) if total > 0 else 0
    
    def get_productivity_score(self):
        if not self.analytics:
            return 0
        return self.analytics.calculate_productivity_score()
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 