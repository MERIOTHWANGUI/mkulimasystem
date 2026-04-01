from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models.product import Product

supplier_bp = Blueprint('supplier', __name__, url_prefix='/supplier')


def supplier_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'supplier':
            flash('Supplier account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


CATEGORIES = ['Seeds', 'Fertilizer', 'Pesticide', 'Tools', 'Equipment', 'Other']
UNITS      = ['per kg', 'per bag (50kg)', 'per bag (90kg)', 'per litre', 'per packet', 'each']
COUNTIES   = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Nyeri',
    'Meru', 'Nyandarua', 'Kiambu', 'Muranga', 'Kirinyaga', 'Embu',
    'Machakos', 'Makueni', 'Kitui', 'Bungoma', 'Kakamega', 'Siaya',
    'Kisii', 'Homa Bay', 'Migori', 'Bomet', 'Kericho', 'Nandi',
    'Uasin Gishu', 'Trans Nzoia', 'Baringo', 'Laikipia', 'Samburu',
    'Turkana', 'Garissa', 'Kwale', 'Kilifi', 'Taita Taveta', 'Other'
]

# What inputs each crop needs — for demand insights
CROP_INPUTS = {
    'Maize':        ['Seeds', 'Fertilizer'],
    'Beans':        ['Seeds', 'Pesticide'],
    'Kale':         ['Seeds', 'Fertilizer', 'Pesticide'],
    'Irish Potato': ['Seeds', 'Fertilizer', 'Pesticide'],
    'Tomato':       ['Seeds', 'Fertilizer', 'Pesticide'],
    'Sorghum':      ['Seeds'],
    'Millet':       ['Seeds'],
    'Groundnut':    ['Seeds', 'Fertilizer'],
    'Cowpea':       ['Seeds'],
    'Soybean':      ['Seeds', 'Fertilizer'],
    'Green Gram':   ['Seeds'],
    'Onion':        ['Seeds', 'Fertilizer', 'Pesticide'],
    'Carrot':       ['Seeds', 'Fertilizer'],
}


@supplier_bp.route('/dashboard')
@login_required
@supplier_required
def dashboard():
    products = Product.query.filter_by(supplier_id=current_user.id)\
                            .order_by(Product.created_at.desc()).all()
    return render_template('supplier/dashboard.html',
                           products=products,
                           categories=CATEGORIES,
                           units=UNITS,
                           counties=COUNTIES)


@supplier_bp.route('/insights')
@login_required
@supplier_required
def insights():
    from app.models.recommendation_history import RecommendationHistory
    from app.models.user import User
    from collections import Counter
    from datetime import datetime, timedelta

    # All recommendations in the system
    all_recs = RecommendationHistory.query.all()

    # Overall crop demand
    crop_counts = Counter(r.top_crop for r in all_recs)
    total_recs  = len(all_recs)

    # Last 30 days trend
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_recs     = [r for r in all_recs if r.created_at >= thirty_days_ago]
    recent_counts   = Counter(r.top_crop for r in recent_recs)

    # Top 5 crops in demand
    top_crops = crop_counts.most_common(5)

    # What the supplier is missing — crops in demand but not stocked
    my_products   = Product.query.filter_by(supplier_id=current_user.id).all()
    my_categories = set(p.category for p in my_products)

    # Opportunity gaps — high demand crops with no matching supplier product
    gaps = []
    for crop, count in crop_counts.most_common():
        needed_inputs = CROP_INPUTS.get(crop, ['Seeds'])
        missing = [i for i in needed_inputs if i not in my_categories]
        if missing:
            gaps.append({
                'crop':    crop,
                'count':   count,
                'missing': missing,
                'pct':     round(count / total_recs * 100, 1) if total_recs else 0,
            })

    # Monthly breakdown for last 6 months
    monthly = {}
    for r in all_recs:
        key = r.created_at.strftime('%b %Y')
        monthly[key] = monthly.get(key, 0) + 1

    # Total farmers
    total_farmers = User.query.filter_by(role='farmer').count()

    return render_template('supplier/insights.html',
                           crop_counts    = crop_counts,
                           top_crops      = top_crops,
                           recent_counts  = recent_counts,
                           total_recs     = total_recs,
                           total_farmers  = total_farmers,
                           gaps           = gaps[:6],
                           monthly        = monthly,
                           my_products    = my_products,
                           CROP_INPUTS    = CROP_INPUTS)


@supplier_bp.route('/product/add', methods=['POST'])
@login_required
@supplier_required
def add_product():
    name        = request.form.get('name',        '').strip()
    category    = request.form.get('category',    '').strip()
    description = request.form.get('description', '').strip()
    price       = request.form.get('price',       '0').strip()
    unit        = request.form.get('unit',        '').strip()
    location    = request.form.get('location',    '').strip()
    phone       = request.form.get('phone',       '').strip()
    image_url   = request.form.get('image_url',   '').strip()

    if not all([name, category, description, price, unit, location, phone]):
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('supplier.dashboard'))

    try:
        price = float(price)
        if price <= 0:
            raise ValueError
    except ValueError:
        flash('Please enter a valid price.', 'danger')
        return redirect(url_for('supplier.dashboard'))

    product = Product(
        supplier_id = current_user.id,
        name        = name,
        category    = category,
        description = description,
        price       = price,
        unit        = unit,
        location    = location,
        phone       = phone,
        image_url   = image_url or None,
        in_stock    = True,
    )
    db.session.add(product)
    db.session.commit()
    flash(f'"{name}" listed successfully!', 'success')
    return redirect(url_for('supplier.dashboard'))


@supplier_bp.route('/product/edit/<int:product_id>', methods=['POST'])
@login_required
@supplier_required
def edit_product(product_id):
    product = Product.query.filter_by(id=product_id, supplier_id=current_user.id).first_or_404()
    product.name        = request.form.get('name',        product.name).strip()
    product.category    = request.form.get('category',    product.category).strip()
    product.description = request.form.get('description', product.description).strip()
    product.unit        = request.form.get('unit',        product.unit).strip()
    product.location    = request.form.get('location',    product.location).strip()
    product.phone       = request.form.get('phone',       product.phone).strip()
    product.image_url   = request.form.get('image_url',   '').strip() or None
    product.in_stock    = request.form.get('in_stock') == 'on'
    try:
        product.price = float(request.form.get('price', product.price))
    except ValueError:
        flash('Invalid price.', 'danger')
        return redirect(url_for('supplier.dashboard'))
    db.session.commit()
    flash(f'"{product.name}" updated!', 'success')
    return redirect(url_for('supplier.dashboard'))


@supplier_bp.route('/product/delete/<int:product_id>', methods=['POST'])
@login_required
@supplier_required
def delete_product(product_id):
    product = Product.query.filter_by(id=product_id, supplier_id=current_user.id).first_or_404()
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'"{name}" removed.', 'info')
    return redirect(url_for('supplier.dashboard'))


@supplier_bp.route('/product/toggle/<int:product_id>', methods=['POST'])
@login_required
@supplier_required
def toggle_stock(product_id):
    product = Product.query.filter_by(id=product_id, supplier_id=current_user.id).first_or_404()
    product.in_stock = not product.in_stock
    db.session.commit()
    status = 'In Stock' if product.in_stock else 'Out of Stock'
    flash(f'"{product.name}" marked as {status}.', 'info')
    return redirect(url_for('supplier.dashboard'))