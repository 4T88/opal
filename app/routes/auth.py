from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models.user import User
from models.analytics import UserAnalytics
from werkzeug.security import generate_password_hash
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password=password  # Password will be hashed by the model
        )
        
        # Create analytics for the user
        analytics = UserAnalytics(user=user)
        
        db.session.add(user)
        db.session.add(analytics)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.verify_password(password):
            login_user(user, remember=remember)
            user.update_last_login()
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user profile
        current_user.full_name = request.form.get('full_name')
        current_user.bio = request.form.get('bio')
        current_user.timezone = request.form.get('timezone')
        
        # Update working hours
        working_hours = {
            'start': request.form.get('working_hours_start'),
            'end': request.form.get('working_hours_end'),
            'days': request.form.getlist('working_days')
        }
        current_user.preferred_working_hours = working_hours
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.verify_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('auth.profile'))
    
    current_user.password = new_password
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('auth.profile'))

@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    if not current_user.verify_password(request.form.get('password')):
        flash('Password is incorrect', 'error')
        return redirect(url_for('auth.profile'))
    
    # Delete user's analytics
    UserAnalytics.query.filter_by(user_id=current_user.id).delete()
    
    # Delete user
    db.session.delete(current_user)
    db.session.commit()
    
    logout_user()
    flash('Your account has been deleted', 'success')
    return redirect(url_for('auth.login')) 