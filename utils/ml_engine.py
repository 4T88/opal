import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Tuple, Optional
import joblib
import os

class MLEngine:
    def __init__(self, model_path: str = 'models/ml_models'):
        self.model_path = model_path
        self.priority_model = None
        self.duration_model = None
        self.scaler = StandardScaler()
        
        # Create model directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)
        
        # Load models if they exist
        self._load_models()
    
    def _load_models(self):
        """Load saved models if they exist"""
        priority_model_path = os.path.join(self.model_path, 'priority_model.joblib')
        duration_model_path = os.path.join(self.model_path, 'duration_model.joblib')
        scaler_path = os.path.join(self.model_path, 'scaler.joblib')
        
        if os.path.exists(priority_model_path):
            self.priority_model = joblib.load(priority_model_path)
        else:
            self.priority_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        if os.path.exists(duration_model_path):
            self.duration_model = joblib.load(duration_model_path)
        else:
            self.duration_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
    
    def _save_models(self):
        """Save trained models"""
        joblib.dump(self.priority_model, os.path.join(self.model_path, 'priority_model.joblib'))
        joblib.dump(self.duration_model, os.path.join(self.model_path, 'duration_model.joblib'))
        joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.joblib'))
    
    def prepare_features(self, task_data: Dict) -> np.ndarray:
        """Prepare features for model input"""
        features = []
        
        # Extract numerical features
        features.extend([
            task_data.get('complexity_score', 0),
            task_data.get('sentiment_score', 0),
            len(task_data.get('keywords', [])),
            task_data.get('estimated_duration', 0) / 60 if task_data.get('estimated_duration') else 0,
        ])
        
        # Add time-based features
        if task_data.get('due_date'):
            days_until_due = (task_data['due_date'] - datetime.utcnow()).days
            features.append(days_until_due)
        else:
            features.append(30)  # Default to 30 days if no due date
        
        # Add categorical features (one-hot encoded)
        categories = ['work', 'personal', 'health', 'learning', 'finance', 'social', 'travel', 'other']
        category = task_data.get('category', 'other')
        features.extend([1 if cat == category else 0 for cat in categories])
        
        return np.array(features).reshape(1, -1)
    
    def train_priority_model(self, historical_data: List[Dict]):
        """Train the priority prediction model"""
        X = []
        y = []
        
        for task in historical_data:
            features = self.prepare_features(task)
            X.append(features[0])
            y.append(task['priority'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.priority_model.fit(X_train_scaled, y_train)
        
        # Save models
        self._save_models()
        
        # Return test score
        return self.priority_model.score(X_test_scaled, y_test)
    
    def train_duration_model(self, historical_data: List[Dict]):
        """Train the duration prediction model"""
        X = []
        y = []
        
        for task in historical_data:
            if task.get('actual_duration'):
                features = self.prepare_features(task)
                X.append(features[0])
                y.append(task['actual_duration'])
        
        if not X:  # No training data
            return 0
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.duration_model.fit(X_train_scaled, y_train)
        
        # Save models
        self._save_models()
        
        # Return test score
        return self.duration_model.score(X_test_scaled, y_test)
    
    def predict_priority(self, task_data: Dict) -> int:
        """Predict task priority (0-5)"""
        features = self.prepare_features(task_data)
        features_scaled = self.scaler.transform(features)
        priority = self.priority_model.predict(features_scaled)[0]
        return int(priority)
    
    def predict_duration(self, task_data: Dict) -> int:
        """Predict task duration in minutes"""
        features = self.prepare_features(task_data)
        features_scaled = self.scaler.transform(features)
        duration = self.duration_model.predict(features_scaled)[0]
        return int(duration)
    
    def analyze_task_patterns(self, historical_data: List[Dict]) -> Dict:
        """Analyze patterns in task completion"""
        if not historical_data:
            return {}
        
        df = pd.DataFrame(historical_data)
        
        patterns = {
            'completion_by_category': {},
            'completion_by_time': {},
            'average_duration_by_category': {},
            'success_rate_by_category': {},
            'common_dependencies': {}
        }
        
        # Analyze completion by category
        if 'category' in df.columns and 'status' in df.columns:
            category_completion = df.groupby('category')['status'].apply(
                lambda x: (x == 'completed').mean()
            ).to_dict()
            patterns['completion_by_category'] = category_completion
        
        # Analyze completion by time of day
        if 'completed_at' in df.columns:
            df['hour'] = pd.to_datetime(df['completed_at']).dt.hour
            time_completion = df.groupby('hour')['status'].apply(
                lambda x: (x == 'completed').mean()
            ).to_dict()
            patterns['completion_by_time'] = time_completion
        
        # Analyze average duration by category
        if 'category' in df.columns and 'actual_duration' in df.columns:
            duration_by_category = df.groupby('category')['actual_duration'].mean().to_dict()
            patterns['average_duration_by_category'] = duration_by_category
        
        # Calculate success rate by category
        if 'category' in df.columns and 'status' in df.columns:
            success_rate = df.groupby('category').apply(
                lambda x: (x['status'] == 'completed').mean()
            ).to_dict()
            patterns['success_rate_by_category'] = success_rate
        
        return patterns
    
    def suggest_optimal_schedule(self, tasks: List[Dict], available_hours: int = 8) -> List[Dict]:
        """Suggest optimal task schedule based on patterns and priorities"""
        if not tasks:
            return []
        
        # Convert tasks to DataFrame for easier manipulation
        df = pd.DataFrame(tasks)
        
        # Calculate priority scores
        df['priority_score'] = df.apply(
            lambda x: self.predict_priority(x.to_dict()), axis=1
        )
        
        # Calculate estimated durations
        df['estimated_duration'] = df.apply(
            lambda x: self.predict_duration(x.to_dict()), axis=1
        )
        
        # Sort tasks by priority and due date
        df = df.sort_values(
            ['priority_score', 'due_date'],
            ascending=[False, True]
        )
        
        # Schedule tasks
        schedule = []
        remaining_hours = available_hours * 60  # Convert to minutes
        
        for _, task in df.iterrows():
            if remaining_hours >= task['estimated_duration']:
                schedule.append(task.to_dict())
                remaining_hours -= task['estimated_duration']
            else:
                break
        
        return schedule
    
    def detect_task_conflicts(self, tasks: List[Dict]) -> List[Dict]:
        """Detect potential conflicts in task scheduling"""
        conflicts = []
        
        # Convert tasks to DataFrame
        df = pd.DataFrame(tasks)
        
        # Check for time conflicts
        if 'due_date' in df.columns and 'estimated_duration' in df.columns:
            df['end_time'] = df['due_date'] + pd.to_timedelta(df['estimated_duration'], unit='minutes')
            
            for i, task1 in df.iterrows():
                for j, task2 in df.iterrows():
                    if i < j:  # Avoid duplicate checks
                        # Check if tasks overlap
                        if (task1['due_date'] <= task2['end_time'] and
                            task2['due_date'] <= task1['end_time']):
                            conflicts.append({
                                'task1': task1.to_dict(),
                                'task2': task2.to_dict(),
                                'type': 'time_conflict',
                                'severity': 'high' if task1['priority'] > 3 or task2['priority'] > 3 else 'medium'
                            })
        
        # Check for resource conflicts
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            for category, count in category_counts.items():
                if count > 3:  # More than 3 tasks in the same category
                    category_tasks = df[df['category'] == category]
                    conflicts.append({
                        'tasks': category_tasks.to_dict('records'),
                        'type': 'resource_conflict',
                        'category': category,
                        'severity': 'medium'
                    })
        
        return conflicts 