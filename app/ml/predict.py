import joblib
import numpy as np
import pandas as pd
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')

# ── METADATA ─────────────────────────────────────────────
CROP_META = {
    'Maize':        {'image': 'maize.png','emoji':'🌽', 'desc': 'Staple grain ideal for mid-altitude warm regions.'},
    'Beans':        {'image':'beans.png','emoji': '🫘', 'desc': 'Legume crop that improves soil nitrogen.'},
    'Sorghum':      {'image':'sorghum.png','emoji': '🌾', 'desc': 'Drought-tolerant grain for dry lowland areas.'},
    'Tomato':       {'image':'tomato.png','emoji': '🍅', 'desc': 'High-value vegetable for warm humid conditions.'},
    'Onion':        {'image':'onion.png','emoji': '🧅', 'desc': 'Cash crop suited for well-drained sandy soils.'},
    'Carrot':       {'image':'carrots.png','emoji': '🥕', 'desc': 'Cool weather root crop for highland areas.'},
    'Millet':       {'image':'millet.png','emoji': '🌾', 'desc': 'Drought-resistant grain for arid regions.'},
    'Groundnut':    {'image':'groundnuts.png','emoji': '🥜', 'desc': 'Legume cash crop rich in protein and oil.'},
    'Soybean':      {'image':'soybean.png','emoji': '🌿', 'desc': 'High-protein legume for warm climates.'},
    'Cowpea':       {'image':'cowpea.png','emoji': '🫘', 'desc': 'Drought-tolerant legume for semi-arid areas.'},
    'Green Gram':   {'image':'greengrams.png','emoji': '🟢', 'desc': 'Fast-maturing legume for hot dry conditions.'},
    'Irish Potato': {'image':'irishpotatoes.png','emoji': '🥔', 'desc': 'High-yield tuber for cool highland areas.'},
    'kale':         {'image':'kale.png','emoji': '🥬', 'desc': 'Nutritious leafy vegetable for highland farms.'},
}

SOIL_MAPPING = {
    'Loamy': 'Loamy', 'loamy': 'Loamy', 'loam': 'Loamy',
    'Sandy-Loam': 'Sandy-Loam', 'Sandy-loam': 'Sandy-Loam', 'sandy-loam': 'Sandy-Loam',
    'Sandy': 'Sandy', 'sandy': 'Sandy',
    'Clay': 'Clay', 'clay': 'Clay',
    'Clay-Loam': 'Clay-Loam', 'clay-loam': 'Clay-Loam',
    'Fertile': 'Fertile', 'fertile': 'Fertile',
    'Alluvial': 'Alluvial', 'alluvial': 'Alluvial',
}

# ── LOAD MODELS ──────────────────────────────────────────
def load_models():
    model         = joblib.load(os.path.join(MODEL_DIR, 'crop_model.pkl'))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    soil_encoder  = joblib.load(os.path.join(MODEL_DIR, 'soil_encoder.pkl'))
    scaler        = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
    return model, label_encoder, soil_encoder, scaler


# ── CORE DECISION FUNCTION ───────────────────────────────
def predict_crops(temperature, rainfall, altitude, soil_type, soil_ph):
    model, label_encoder, soil_encoder, scaler = load_models()

    # ── INPUT CLEANING ────────────────────────────────────
    clean_soil = SOIL_MAPPING.get(soil_type, 'Loamy')
    try:
        soil_encoded = soil_encoder.transform([clean_soil])[0]
    except ValueError:
        soil_encoded = 0

    features = pd.DataFrame(
        [[temperature, rainfall, altitude, soil_encoded, soil_ph]],
        columns=['Temperature', 'Rainfall', 'Altitude', 'Soil_encoded', 'Soil_pH']
    )

    features_scaled = scaler.transform(features)
    raw_probs = model.predict_proba(features_scaled)[0]
    classes = label_encoder.classes_
    # Mild probability smoothing to reduce dominance by a single class.
    def _normalize_probs(probs):
        total = float(np.sum(probs))
        if total <= 0:
            return np.ones_like(probs) / len(probs)
        return probs / total

    def _smooth_probs(probs, temperature=1.25, uniform_mix=0.06):
        # Temperature > 1.0 flattens overconfident distributions.
        probs = np.clip(probs, 1e-9, 1.0)
        if temperature and temperature != 1.0:
            probs = probs ** (1.0 / temperature)
        probs = _normalize_probs(probs)
        if uniform_mix and uniform_mix > 0:
            uniform = np.full_like(probs, 1.0 / len(probs))
            probs = (1.0 - uniform_mix) * probs + uniform_mix * uniform
        return _normalize_probs(probs)

    balanced_probs = _smooth_probs(raw_probs)

    # ── AGRONOMIC RULES ───────────────────────────────────
    RULES = {
        'Tomato': {'temp': (18, 30), 'rain': (400, 1200), 'ph': (5.5, 7.5)},
        'Maize': {'temp': (15, 30), 'rain': (500, 1500), 'ph': (5.5, 7.5)},
        'Beans': {'temp': (15, 25), 'rain': (300, 800), 'ph': (6, 7)},
        'Sorghum': {'temp': (20, 35), 'rain': (250, 800), 'ph': (5, 8)},
        'Irish Potato': {'temp': (10, 25), 'rain': (600, 1200), 'ph': (5, 6.5)},
    }

    def suitability(crop):
        if crop not in RULES:
            return 0.5

        r = RULES[crop]
        score = 0

        if r['temp'][0] <= temperature <= r['temp'][1]:
            score += 1
        if r['rain'][0] <= rainfall <= r['rain'][1]:
            score += 1
        if r['ph'][0] <= soil_ph <= r['ph'][1]:
            score += 1

        return score / 3

    def risk(crop):
        r = 0

        if rainfall < 400:
            r += 2
        if temperature > 35:
            r += 1
        if soil_ph < 5 or soil_ph > 8:
            r += 1

        return r

    def explain(suit, rsk):
        reasons = []

        if suit >= 0.7:
            reasons.append("Good environmental match")

        if suit < 0.4:
            reasons.append("Poor environmental match")

        if rsk >= 2:
            reasons.append("High environmental risk")

        if rsk == 0:
            reasons.append("Low risk option")

        return reasons

    def confidence(prob, suit):
        if prob > 0.6 and suit > 0.7:
            return "Strong"
        elif prob > 0.4:
            return "Moderate"
        else:
            return "Weak"

    # ── DECISION ENGINE ───────────────────────────────────
    results = []

    for crop, prob in zip(classes, balanced_probs):
        suit = suitability(crop)
        rsk = risk(crop)

        final_score = (0.4 * prob) + (0.6 * suit)

        entry = {
            'crop': crop,
            # Cast to native Python float for DB/JSON compatibility
            'ml_prob': float(round(prob * 100, 2)),
            'suitability': float(round(suit, 2)),
            'final_score': float(round(final_score * 100, 2)),
            'risk': int(rsk),
            'confidence': confidence(prob, suit),
            'reasons': explain(suit, rsk)
        }

        meta = CROP_META.get(crop, {
            'image': 'default.png',
            'emoji': '🌿',
            'desc': ''
        })

        entry.update(meta)

        results.append(entry)
    # Sort by decision score
    results = sorted(results, key=lambda x: x['final_score'], reverse=True)

    # ── STRATEGIC OUTPUT ──────────────────────────────────
    decision = {
        "primary": results[0],
        "secondary": results[1] if len(results) > 1 else None,
        "low_risk_option": min(results, key=lambda x: x['risk']),
        "top_options": results[:5]
    }

    # ── ALERTS ────────────────────────────────────────────
    alerts = []

    if rainfall < 400:
        alerts.append("⚠️ Low rainfall – irrigation required")

    if temperature > 35:
        alerts.append("⚠️ High temperature – heat stress risk")

    if soil_ph < 5 or soil_ph > 8:
        alerts.append("⚠️ Soil pH is outside optimal range")

    decision["alerts"] = alerts

    return decision
