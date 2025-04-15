from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .models import db
from sqlalchemy import or_
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
from flask import abort
from flask_cors import CORS


auth = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrap


@auth.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password     = request.form.get('password')

        user = User.query.filter(or_(User.email == identifier, User.name == identifier)).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", user=current_user)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_admin = request.form.get('is_admin') == 'on'

        if not email or not password or not confirm_password:
            flash('Vui lòng điền đầy đủ thông tin!', category='error')
            return redirect(url_for('auth.sign_up'))

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', category='error')
            return redirect(url_for('auth.sign_up'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email đã được sử dụng!', category='error')
            return redirect(url_for('auth.sign_up'))

        new_user = User(
            email=email,
            name=name,
            is_admin=is_admin
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công!', category='success')
        return redirect(url_for('auth.login'))

    return render_template('sign-up.html', user=current_user)

@auth.route('/logout')

@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/dashboard')

@login_required
@admin_required
def dashboard():
    users = User.query.all()
    return render_template("dashboard.html", user=users)

@auth.route('/hr_management', methods=['GET', 'POST'])

@login_required
@admin_required
def hr_management():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            email = request.form.get('email')
            name = request.form.get('name')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            is_admin = request.form.get('is_admin') == 'on'

            if len(email) < 4:
                flash('Email must be greater than 4 characters.', category='error')
            elif len(password) < 6:
                flash('Password must be greater than 6 characters.', category='error')
            elif password != confirm_password:
                flash('Passwords do not match.', category='error')
            else:
                new_user = User(email=email, name=name, 
                                password=generate_password_hash(password, method='pbkdf2:sha256'), 
                                is_admin=is_admin)
                db.session.add(new_user)
                db.session.commit()
                flash('Account created!', category='success')
        elif action == 'edit':
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            if user:
                user.email = request.form.get('email')
                user.name = request.form.get('name')
                user.is_admin = request.form.get('is_admin') == 'on'
                db.session.commit()
                flash('User updated!', category='success')
                return jsonify(success=True)
            else:
                flash('user not found!', category='error')
                return jsonify(success=False, error='User not found')
        elif action == 'delete':
            user_id = request.form.get('user_id')
            user = User.query.filter_by(id=user_id).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                flash('User deleted!', category='success')
                return jsonify(success=True)
            else:
                return jsonify(success=False, error='User not found')
        return redirect(url_for('auth.hr_management'))

    users = User.query.all()
    return render_template("HR_management.html", user=users)    


CORS(auth, supports_credentials=True)

@auth.route('/api/user', methods=['GET'])

@login_required
def get_user():
    user = {
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'is_admin': current_user.is_admin
    }
    return jsonify(user)