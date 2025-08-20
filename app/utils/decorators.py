from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def admin_required(f):
    """
    Decorator to check if the current user is an admin.
    Use this decorator on admin routes to ensure only admin users can access them.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.can_access_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('views.home'))
        
        return f(*args, **kwargs)
    return decorated_function


