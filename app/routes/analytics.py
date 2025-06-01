from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.analytics import UserAnalytics
from models.task import Task
from utils.data_visualizer import DataVisualizer
from utils.ml_engine import MLEngine
from datetime import datetime, timedelta
import json

bp = Blueprint('analytics', __name__)
data_visualizer = DataVisualizer()
ml_engine = MLEngine()

@bp.route('/analytics/dashboard')
@login_required
def dashboard():
    # Get user's analytics
    analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
    
    # Create productivity dashboard
    dashboard = data_visualizer.create_productivity_dashboard(analytics.to_dict())
    
    # Get performance metrics
    metrics = data_visualizer.create_performance_metrics(analytics.to_dict())
    
    return render_template('analytics/dashboard.html', dashboard=dashboard, metrics=metrics)

@bp.route('/analytics/task-analysis')
@login_required
def task_analysis():
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Create task analysis report
    report = data_visualizer.create_task_analysis_report(task_data)
    
    return render_template('analytics/task_analysis.html', report=report)

@bp.route('/analytics/productivity-timeline')
@login_required
def productivity_timeline():
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Create task timeline
    timeline = data_visualizer.create_task_timeline(task_data)
    
    return render_template('analytics/productivity_timeline.html', timeline=timeline)

@bp.route('/analytics/productivity-heatmap')
@login_required
def productivity_heatmap():
    # Get user's analytics
    analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
    
    # Create productivity heatmap
    heatmap = data_visualizer.create_productivity_heatmap(analytics.to_dict())
    
    return render_template('analytics/productivity_heatmap.html', heatmap=heatmap)

@bp.route('/analytics/task-patterns')
@login_required
def task_patterns():
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Analyze task patterns
    patterns = ml_engine.analyze_task_patterns(task_data)
    
    return render_template('analytics/task_patterns.html', patterns=patterns)

@bp.route('/analytics/completion-trends')
@login_required
def completion_trends():
    # Get tasks completed in the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    completed_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == 'completed',
        Task.completed_at >= thirty_days_ago
    ).order_by(Task.completed_at.asc()).all()
    
    # Group tasks by completion date
    completion_data = {}
    for task in completed_tasks:
        date = task.completed_at.date().isoformat()
        if date not in completion_data:
            completion_data[date] = 0
        completion_data[date] += 1
    
    return jsonify(completion_data)

@bp.route('/analytics/category-performance')
@login_required
def category_performance():
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Analyze patterns
    patterns = ml_engine.analyze_task_patterns(task_data)
    
    # Extract category performance data
    category_data = {
        'completion_rates': patterns.get('completion_by_category', {}),
        'average_durations': patterns.get('average_duration_by_category', {}),
        'success_rates': patterns.get('success_rate_by_category', {})
    }
    
    return jsonify(category_data)

@bp.route('/analytics/time-distribution')
@login_required
def time_distribution():
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Analyze patterns
    patterns = ml_engine.analyze_task_patterns(task_data)
    
    return jsonify(patterns.get('completion_by_time', {}))

@bp.route('/analytics/export-data')
@login_required
def export_data():
    # Get user's analytics
    analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
    
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Prepare export data
    export_data = {
        'analytics': analytics.to_dict(),
        'tasks': [task.to_dict() for task in tasks],
        'export_date': datetime.utcnow().isoformat()
    }
    
    return jsonify(export_data)

@bp.route('/analytics/suggestions')
@login_required
def get_suggestions():
    # Get user's analytics
    analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
    
    # Get all tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Analyze patterns
    patterns = ml_engine.analyze_task_patterns(task_data)
    
    # Generate suggestions based on patterns
    suggestions = []
    
    # Check completion rate
    if analytics.completion_rate < 70:
        suggestions.append({
            'type': 'completion_rate',
            'message': 'Your task completion rate is below 70%. Consider breaking down tasks into smaller, more manageable pieces.',
            'severity': 'high'
        })
    
    # Check category distribution
    category_completion = patterns.get('completion_by_category', {})
    for category, rate in category_completion.items():
        if rate < 0.5:
            suggestions.append({
                'type': 'category_performance',
                'message': f'You have a low completion rate in the {category} category. Consider reviewing your approach to these tasks.',
                'severity': 'medium'
            })
    
    # Check time management
    time_completion = patterns.get('completion_by_time', {})
    if time_completion:
        max_hour = max(time_completion.items(), key=lambda x: x[1])[0]
        suggestions.append({
            'type': 'time_management',
            'message': f'You are most productive during hour {max_hour}. Try to schedule important tasks during this time.',
            'severity': 'low'
        })
    
    return jsonify(suggestions) 