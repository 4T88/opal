from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models.task import Task, TaskDependency
from models.analytics import UserAnalytics
from utils.nlp_processor import NLPProcessor
from utils.ml_engine import MLEngine
from datetime import datetime
import json

bp = Blueprint('tasks', __name__)
nlp_processor = NLPProcessor()
ml_engine = MLEngine()

@bp.route('/tasks')
@login_required
def task_list():
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    priority = request.args.get('priority', 'all')
    
    # Base query
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(status=status)
    if category != 'all':
        query = query.filter_by(category=category)
    if priority != 'all':
        query = query.filter_by(priority=int(priority))
    
    tasks = query.order_by(Task.due_date.asc()).all()
    return render_template('tasks/list.html', tasks=tasks)

@bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        # Process natural language input
        task_data = nlp_processor.process_task_input(request.form.get('description'))
        
        # Create new task
        task = Task(
            title=task_data['title'],
            description=task_data['description'],
            due_date=task_data['due_date'],
            category=task_data['category'],
            complexity_score=task_data['complexity_score'],
            sentiment_score=task_data['sentiment_score'],
            keywords=json.dumps(task_data['keywords']),
            estimated_duration=task_data['estimated_duration'],
            user_id=current_user.id
        )
        
        # Predict priority using ML
        task.priority = ml_engine.predict_priority(task_data)
        
        # Update user's analytics
        analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
        analytics.total_tasks_created += 1
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully', 'success')
        return redirect(url_for('tasks.task_list'))
    
    return render_template('tasks/create.html')

@bp.route('/tasks/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    # Get task suggestions
    suggestions = nlp_processor.suggest_task_improvements(task.description)
    
    # Get dependent tasks
    dependent_tasks = task.get_dependent_tasks()
    
    return render_template('tasks/view.html', task=task, suggestions=suggestions, dependent_tasks=dependent_tasks)

@bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    if request.method == 'POST':
        # Update task
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        task.category = request.form.get('category')
        task.priority = int(request.form.get('priority'))
        task.estimated_duration = int(request.form.get('estimated_duration'))
        
        # Update tags
        tags = request.form.get('tags', '').split(',')
        task.tags = json.dumps([tag.strip() for tag in tags if tag.strip()])
        
        db.session.commit()
        flash('Task updated successfully', 'success')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    return render_template('tasks/edit.html', task=task)

@bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully', 'success')
    return redirect(url_for('tasks.task_list'))

@bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    task.status = 'completed'
    task.completed_at = datetime.utcnow()
    
    # Update analytics
    analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
    analytics.update_completion_metrics(task)
    
    db.session.commit()
    flash('Task marked as completed', 'success')
    return redirect(url_for('tasks.task_list'))

@bp.route('/tasks/<int:task_id>/add-dependency', methods=['POST'])
@login_required
def add_dependency(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    dependent_task_id = request.form.get('dependent_task_id')
    dependent_task = Task.query.get_or_404(dependent_task_id)
    
    if dependent_task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    try:
        task.add_dependency(dependent_task)
        db.session.commit()
        flash('Dependency added successfully', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('tasks.view_task', task_id=task.id))

@bp.route('/tasks/<int:task_id>/remove-dependency/<int:dependent_task_id>', methods=['POST'])
@login_required
def remove_dependency(task_id, dependent_task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('tasks.task_list'))
    
    dependent_task = Task.query.get_or_404(dependent_task_id)
    task.remove_dependency(dependent_task)
    db.session.commit()
    
    flash('Dependency removed successfully', 'success')
    return redirect(url_for('tasks.view_task', task_id=task.id))

@bp.route('/tasks/suggest-schedule', methods=['GET'])
@login_required
def suggest_schedule():
    available_hours = int(request.args.get('hours', 8))
    
    # Get all pending tasks
    tasks = Task.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Get suggested schedule
    schedule = ml_engine.suggest_optimal_schedule(task_data, available_hours)
    
    return jsonify(schedule)

@bp.route('/tasks/analyze-conflicts', methods=['GET'])
@login_required
def analyze_conflicts():
    # Get all pending tasks
    tasks = Task.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).all()
    
    # Convert tasks to dictionary format
    task_data = [task.to_dict() for task in tasks]
    
    # Detect conflicts
    conflicts = ml_engine.detect_task_conflicts(task_data)
    
    return jsonify(conflicts)

@bp.route('/tasks/bulk-update', methods=['POST'])
@login_required
def bulk_update():
    task_ids = request.form.getlist('task_ids')
    action = request.form.get('action')
    
    if not task_ids:
        flash('No tasks selected', 'error')
        return redirect(url_for('tasks.task_list'))
    
    tasks = Task.query.filter(
        Task.id.in_(task_ids),
        Task.user_id == current_user.id
    ).all()
    
    if action == 'complete':
        for task in tasks:
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            
            # Update analytics
            analytics = UserAnalytics.query.filter_by(user_id=current_user.id).first()
            analytics.update_completion_metrics(task)
    
    elif action == 'delete':
        for task in tasks:
            db.session.delete(task)
    
    elif action == 'archive':
        for task in tasks:
            task.status = 'archived'
    
    db.session.commit()
    flash(f'Tasks {action}d successfully', 'success')
    return redirect(url_for('tasks.task_list')) 