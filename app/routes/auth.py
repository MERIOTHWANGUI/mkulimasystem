from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


def redirect_by_role(user):
    print(f"DEBUG role: {user.role}") 
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    if user.is_supplier():
        return redirect(url_for('supplier.dashboard'))
    return redirect(url_for('farmer.dashboard'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name',  '').strip()
        username   = request.form.get('username',   '').strip()
        email      = request.form.get('email',      '').strip().lower()
        password   = request.form.get('password',   '')
        role       = request.form.get('role', 'farmer')

        if not all([first_name, last_name, username, email, password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')

        if role not in ('farmer', 'supplier'):
            role = 'farmer'

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('auth/register.html')

        new_user = User(
            first_name = first_name,
            last_name  = last_name,
            username   = username,
            email      = email,
            password   = generate_password_hash(password),
            role       = role,
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f'Welcome, {first_name}! Account created — please log in. 🌱', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password   = request.form.get('password', '')
        remember   = request.form.get('remember') == 'on'

        if not identifier or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.first_name}! 🌱', 'success')
            return redirect_by_role(user)
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out. See you next season! 🌾', 'info')
    return redirect(url_for('main.index'))