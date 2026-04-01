from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models.user import User
import json
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

KB_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'knowledge_base.json')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


def load_kb():
    try:
        with open(KB_PATH, 'r') as f:
            return json.load(f)
    except:
        return []


def save_kb(data):
    with open(KB_PATH, 'w') as f:
        json.dump(data, f, indent=2)


# ── DASHBOARD / KB MANAGER ──
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    entries = load_kb()
    # Stats
    total_users     = User.query.count()
    total_farmers   = User.query.filter_by(role='farmer').count()
    total_suppliers = User.query.filter_by(role='supplier').count()
    return render_template('admin/dashboard.html',
                           entries=entries,
                           total_users=total_users,
                           total_farmers=total_farmers,
                           total_suppliers=total_suppliers)


# ── KB ROUTES ──
@admin_bp.route('/kb/add', methods=['POST'])
@login_required
@admin_required
def kb_add():
    topic   = request.form.get('topic', '').strip()
    content = request.form.get('content', '').strip()
    if not topic or not content:
        flash('Topic and content are required.', 'danger')
        return redirect(url_for('admin.dashboard'))
    entries = load_kb()
    new_id  = max((e['id'] for e in entries), default=0) + 1
    entries.append({'id': new_id, 'topic': topic, 'content': content})
    save_kb(entries)
    flash(f'"{topic}" added successfully!', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/kb/edit/<int:entry_id>', methods=['POST'])
@login_required
@admin_required
def kb_edit(entry_id):
    topic   = request.form.get('topic', '').strip()
    content = request.form.get('content', '').strip()
    entries = load_kb()
    for e in entries:
        if e['id'] == entry_id:
            e['topic']   = topic
            e['content'] = content
            break
    save_kb(entries)
    flash(f'"{topic}" updated!', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/kb/delete/<int:entry_id>', methods=['POST'])
@login_required
@admin_required
def kb_delete(entry_id):
    entries = [e for e in load_kb() if e['id'] != entry_id]
    save_kb(entries)
    flash('Entry deleted.', 'info')
    return redirect(url_for('admin.dashboard'))


# ── USER MANAGEMENT ──
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    from app.models.recommendation_history import RecommendationHistory
    from app.models.product import Product

    all_users = User.query.order_by(User.created_at.desc()).all()

    # Attach stats to each user
    for u in all_users:
        if u.role == 'farmer':
            u.rec_count = RecommendationHistory.query.filter_by(farmer_id=u.id).count()
        elif u.role == 'supplier':
            u.product_count = Product.query.filter_by(supplier_id=u.id).count()

    farmers   = [u for u in all_users if u.role == 'farmer']
    suppliers = [u for u in all_users if u.role == 'supplier']
    admins    = [u for u in all_users if u.role == 'admin']

    return render_template('admin/users.html',
                           all_users=all_users,
                           farmers=farmers,
                           suppliers=suppliers,
                           admins=admins)


@admin_bp.route('/users/change-role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('admin.users'))
    new_role = request.form.get('role')
    if new_role not in ('farmer', 'supplier', 'admin'):
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin.users'))
    user.role = new_role
    db.session.commit()
    flash(f'{user.first_name} is now a {new_role}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    name = f'{user.first_name} {user.last_name}'
    db.session.delete(user)
    db.session.commit()
    flash(f'{name} has been deleted.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not getattr(user, 'is_active', True)
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'{user.first_name} has been {status}.', 'info')
    return redirect(url_for('admin.users'))