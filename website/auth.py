from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
from sqlalchemy import or_
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
from flask import abort

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
        password = request.form.get('password')

        user = User.query.filter(or_(User.email == identifier, User.username == identifier)).first()
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

@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_admin = request.form.get('is_admin') == 'on'
        admin_id = current_user.id if is_admin else None

        if len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(password) < 6:
            flash('Password must be greater than 6 characters.', category='error')
        elif password != confirm_password:
            flash('Passwords do not match.', category='error')
        else:
            new_user = User(email=email, username=username, 
                            password=generate_password_hash(password, method='pbkdf2:sha256'), 
                            is_admin=is_admin,
                            admin_id=admin_id)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))
    return render_template("sign-up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.filter_by(admin_id=current_user.id).all()
    return render_template("dashboard.html", user=users)