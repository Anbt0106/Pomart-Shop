from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_login import login_user, logout_user, login_required, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email_or_username = data.get('email', '')
        password = data.get('password', '')
        
        # Thử tìm user bằng email trước, nếu không có thì tìm bằng username
        user = User.query.filter_by(email=email_or_username).first()
        if not user:
            user = User.query.filter_by(username=email_or_username).first()
            
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash('Logged in successfully!', category='success')
            return redirect(url_for('views.home'))
        else:
            flash('Invalid email/username or password', category='error')
    
    return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        data = request.form
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        username = data.get('username', '')
        email = data.get('email', '')
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        if not first_name or len(first_name) < 2:
            flash('First name must be at least 2 characters long', category='error')
        elif not last_name or len(last_name) < 2:
            flash('Last name must be at least 2 characters long', category='error')
        elif not username or len(username) < 3:
            flash('Username must be at least 3 characters long', category='error')
        elif len(email) < 5:
            flash('Email must be at least 5 characters long', category='error')
        elif password != confirm_password:
            flash('Passwords don\'t match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', category='error')
        else: 
            user = User.query.filter_by(email=email).first()
            username_exists = User.query.filter_by(username=username).first()
            
            if user:
                flash('Email already exists', category='error')
            elif username_exists:
                flash('Username already exists', category='error')
            else:
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                new_user = User(first_name=first_name, last_name=last_name, username=username, email=email, password_hash=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                flash('Account created successfully!', category='success')
                return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth.route('/admin') #Dashboard
@login_required
def admin():
    # Kiểm tra user có thể truy cập admin panel không
    if not current_user.can_access_admin():
        return redirect(url_for('views.home'))
    
    return render_template('admin/admin.html')

@auth.route('/account')
@login_required
def account():
    """User account page"""
    return render_template('account.html')

@auth.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()

        # Validation
        if not first_name or len(first_name) < 2:
            flash('Tên phải có ít nhất 2 ký tự', 'error')
            return redirect(url_for('auth.account'))

        if not last_name or len(last_name) < 2:
            flash('Họ phải có ít nhất 2 ký tự', 'error')
            return redirect(url_for('auth.account'))

        if not username or len(username) < 3:
            flash('Tên đăng nhập phải có ít nhất 3 ký tự', 'error')
            return redirect(url_for('auth.account'))

        if not email or len(email) < 5:
            flash('Email không hợp lệ', 'error')
            return redirect(url_for('auth.account'))

        # Check if username or email already exists (exclude current user)
        existing_username = User.query.filter(User.username == username, User.id != current_user.id).first()
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()

        if existing_username:
            flash('Tên đăng nhập đã tồn tại', 'error')
            return redirect(url_for('auth.account'))

        if existing_email:
            flash('Email đã tồn tại', 'error')
            return redirect(url_for('auth.account'))

        # Update user information
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.username = username
        current_user.email = email

        db.session.commit()
        flash('Cập nhật thông tin thành công!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi cập nhật thông tin', 'error')
        print(f"Error updating profile: {e}")

    return redirect(url_for('auth.account'))

@auth.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not current_password:
            flash('Vui lòng nhập mật khẩu hiện tại', 'error')
            return redirect(url_for('auth.account'))

        if not check_password_hash(current_user.password_hash, current_password):
            flash('Mật khẩu hiện tại không đúng', 'error')
            return redirect(url_for('auth.account'))

        if len(new_password) < 8:
            flash('Mật khẩu mới phải có ít nhất 8 ký tự', 'error')
            return redirect(url_for('auth.account'))

        if new_password != confirm_password:
            flash('Mật khẩu mới không khớp', 'error')
            return redirect(url_for('auth.account'))

        # Update password
        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()

        flash('Đổi mật khẩu thành công!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi đổi mật khẩu', 'error')
        print(f"Error changing password: {e}")

    return redirect(url_for('auth.account'))
