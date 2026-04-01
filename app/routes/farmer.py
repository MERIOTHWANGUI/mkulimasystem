from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from dotenv import load_dotenv
from groq import Groq
from app.ml.predict import predict_crops
from app.extensions import db
import json
import os

load_dotenv()

farmer_bp = Blueprint('farmer', __name__, url_prefix='/farmer')


def farmer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_farmer():
            flash('This area is for farmers only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── DASHBOARD + AUTO-SAVE ──
@farmer_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
@farmer_required
def dashboard():
    from app.models.recommendation_history import RecommendationHistory

    results   = None
    form_data = {}
    error     = None

    if request.method == 'POST':
        try:
            temperature = float(request.form.get('temperature', 20))
            rainfall    = float(request.form.get('rainfall',    800))
            altitude    = float(request.form.get('altitude',    1200))
            soil_type   = request.form.get('soil_type', 'Loamy')
            soil_ph     = float(request.form.get('soil_ph',     6.5))

            form_data = {
                'temperature': temperature,
                'rainfall':    rainfall,
                'altitude':    altitude,
                'soil_type':   soil_type,
                'soil_ph':     soil_ph,
            }

            results = predict_crops(temperature, rainfall, altitude, soil_type, soil_ph)

            # ── AUTO-SAVE recommendation to history ──
            if results:
                top = results[0]
                rec = RecommendationHistory(
                    farmer_id      = current_user.id,
                    temperature    = temperature,
                    rainfall       = rainfall,
                    altitude       = altitude,
                    soil_type      = soil_type,
                    soil_ph        = soil_ph,
                    top_crop       = top['crop'],
                    top_confidence = top['percentage'],
                )
                rec.set_results(results)
                db.session.add(rec)
                db.session.commit()

        except Exception as e:
            error = f'Could not get recommendation: {str(e)}'

    return render_template(
        'farmer/dashboard.html',
        results=results,
        form_data=form_data,
        error=error
    )


# ── REPORTS PAGE ──
# ── REPLACE your reports() route in farmer.py with this ──

@farmer_bp.route('/reports')
@login_required
@farmer_required
def reports():
    from app.models.recommendation_history import RecommendationHistory
    from app.models.chat_history import ChatHistory
    from collections import OrderedDict

    # ── CROP HISTORY ──
    history = RecommendationHistory.query\
        .filter_by(farmer_id=current_user.id)\
        .order_by(RecommendationHistory.created_at.desc())\
        .all()

    for rec in history:
        rec.results = rec.get_results()

    total_checks = len(history)
    crop_counts  = {}
    for rec in history:
        crop_counts[rec.top_crop] = crop_counts.get(rec.top_crop, 0) + 1

    most_recommended = max(crop_counts, key=crop_counts.get) if crop_counts else None
    avg_confidence   = round(
        sum(r.top_confidence for r in history) / total_checks, 1
    ) if total_checks > 0 else 0

    # ── CHAT HISTORY ──
    chats = ChatHistory.query\
        .filter_by(farmer_id=current_user.id)\
        .order_by(ChatHistory.created_at.asc())\
        .all()

    # Group chats by date
    chat_days = OrderedDict()
    for msg in chats:
        day = msg.created_at.strftime('%A, %d %B %Y')
        if day not in chat_days:
            chat_days[day] = []
        chat_days[day].append(msg)

    return render_template(
        'farmer/reports.html',
        history          = history,
        total_checks     = total_checks,
        most_recommended = most_recommended,
        crop_counts      = crop_counts,
        avg_confidence   = avg_confidence,
        chat_days        = chat_days,
        chat_count       = len(chats),
    )


# ── PDF EXPORT ──
@farmer_bp.route('/reports/pdf')
@login_required
@farmer_required
def download_report_pdf():
    from app.models.recommendation_history import RecommendationHistory
    from app.utils.report import generate_history_pdf

    history = RecommendationHistory.query\
        .filter_by(farmer_id=current_user.id)\
        .order_by(RecommendationHistory.created_at.desc())\
        .all()

    for rec in history:
        rec.results = rec.get_results()

    if not history:
        flash('No recommendations yet. Run the crop advisor first!', 'warning')
        return redirect(url_for('farmer.reports'))

    crop_counts = {}
    for rec in history:
        crop = rec.top_crop
        crop_counts[crop] = crop_counts.get(crop, 0) + 1

    buffer = generate_history_pdf(
        farmer      = current_user,
        history     = history,
        crop_counts = crop_counts,
    )

    filename = f'AgroSense_Report_{current_user.username}.pdf'
    return send_file(
        buffer,
        mimetype     = 'application/pdf',
        as_attachment= True,
        download_name= filename,
    )


# ── DELETE A SINGLE RECORD ──
@farmer_bp.route('/reports/delete/<int:rec_id>', methods=['POST'])
@login_required
@farmer_required
def delete_record(rec_id):
    from app.models.recommendation_history import RecommendationHistory
    rec = RecommendationHistory.query.filter_by(
        id=rec_id, farmer_id=current_user.id).first_or_404()
    db.session.delete(rec)
    db.session.commit()
    flash('Record deleted.', 'info')
    return redirect(url_for('farmer.reports'))


# ── CHATBOT PAGE ──
# ── CHAT API — replace your existing chat() route with this ──

# ── CHATBOT PAGE ──
@farmer_bp.route('/chatbot')
@login_required
@farmer_required
def chatbot():
    return render_template('farmer/chatbot.html')


# ── CHAT API ──
@farmer_bp.route('/chat', methods=['POST'])
@login_required
@farmer_required
def chat():
    from app.models.chat_history import ChatHistory

    data    = request.get_json()
    message = data.get('message', '').strip()
    history = data.get('history', [])
    context = data.get('context', '')

    if not message:
        return jsonify({'reply': 'Please type a message.'})

    kb_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'knowledge_base.json')
    try:
        with open(kb_path, 'r') as f:
            kb_data = json.load(f)
        knowledge = '\n'.join([f"{e['topic']}: {e['content']}" for e in kb_data])
    except:
        kb_data   = []
        knowledge = ''

    groq_key = os.getenv('GROQ_API_KEY')

    def save_messages(user_msg, bot_reply):
        """Save both sides of the conversation to DB."""
        try:
            db.session.add(ChatHistory(farmer_id=current_user.id, role='user',      message=user_msg))
            db.session.add(ChatHistory(farmer_id=current_user.id, role='assistant',  message=bot_reply))
            db.session.commit()
        except:
            db.session.rollback()

    try:
        if not groq_key:
            raise Exception("No API key")

        client = Groq(api_key=groq_key)

        system_prompt = f"""You are AgriBot, a friendly farming helper for Kenyan farmers.
Talk like a friend texting them — very short, very simple, warm.
Maximum 2-3 short sentences per reply. Never more.
Use very simple English that a standard 7 farmer can understand.
Always reply in English only.
No lists, no steps, no bold text, no formatting at all — just plain friendly sentences.
End with a short follow-up question to keep the conversation going.
Use this farming knowledge to answer accurately:
{knowledge}
{f"This farmer got these crop results: {context}" if context else ""}"""

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            messages.append({"role": h['role'], "content": h['content']})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        save_messages(message, reply)
        return jsonify({'reply': reply})

    except Exception:
        msg_lower  = message.lower()
        best_entry = None
        best_score = 0

        for entry in kb_data:
            score = 0
            for word in entry['topic'].lower().split():
                if word in msg_lower and len(word) > 3:
                    score += 10
            for word in msg_lower.split():
                if len(word) > 3 and word in entry['content'].lower():
                    score += 1
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score > 0:
            sentences = best_entry['content'].split('.')
            reply     = '. '.join(sentences[:2]).strip() + '.'
        else:
            reply = "I can help with planting, soil, pests and markets in Kenya. What crop or topic are you asking about?"

        save_messages(message, reply)
        return jsonify({'reply': reply})


# ── MARKETPLACE ──
@farmer_bp.route('/marketplace')
@login_required
@farmer_required
def marketplace():
    from app.models.product import Product
    products   = Product.query.filter_by(in_stock=True)\
                              .order_by(Product.created_at.desc()).all()
    categories = sorted(list({p.category for p in products}))
    locations  = sorted(list({p.location for p in products}))
    return render_template('farmer/marketplace.html',
                           products=products,
                           categories=categories,
                           locations=locations)