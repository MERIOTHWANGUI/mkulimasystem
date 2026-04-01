import joblib
import numpy as np
import pandas as pd
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')

CROP_META = {
    'Maize':        {'emoji': '🌽', 'desc': 'Staple grain ideal for mid-altitude warm regions.'},
    'Beans':        {'emoji': '🫘', 'desc': 'Legume crop that improves soil nitrogen.'},
    'Sorghum':      {'emoji': '🌾', 'desc': 'Drought-tolerant grain for dry lowland areas.'},
    'Tomato':       {'emoji': '🍅', 'desc': 'High-value vegetable for warm humid conditions.'},
    'Onion':        {'emoji': '🧅', 'desc': 'Cash crop suited for well-drained sandy soils.'},
    'Carrot':       {'emoji': '🥕', 'desc': 'Cool weather root crop for highland areas.'},
    'Millet':       {'emoji': '🌾', 'desc': 'Drought-resistant grain for arid regions.'},
    'Groundnut':    {'emoji': '🥜', 'desc': 'Legume cash crop rich in protein and oil.'},
    'Soybean':      {'emoji': '🌿', 'desc': 'High-protein legume for warm climates.'},
    'Cowpea':       {'emoji': '🫘', 'desc': 'Drought-tolerant legume for semi-arid areas.'},
    'Green Gram':   {'emoji': '🟢', 'desc': 'Fast-maturing legume for hot dry conditions.'},
    'Irish Potato': {'emoji': '🥔', 'desc': 'High-yield tuber for cool highland areas.'},
    'kale':         {'emoji': '🥬', 'desc': 'Nutritious leafy vegetable for highland farms.'},
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


def load_models():
    model         = joblib.load(os.path.join(MODEL_DIR, 'crop_model.pkl'))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    soil_encoder  = joblib.load(os.path.join(MODEL_DIR, 'soil_encoder.pkl'))
    scaler        = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
    return model, label_encoder, soil_encoder, scaler


def predict_crops(temperature, rainfall, altitude, soil_type, soil_ph):
    model, label_encoder, soil_encoder, scaler = load_models()

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

    # ── SHARPENING ──────────────────────────────────────────────
    # Power of 4 makes best crop dominate clearly
    # e.g. [0.4, 0.3, 0.2] → after sharpen → [0.7, 0.2, 0.08]
    sharp = np.power(raw_probs, 4)
    sharp = sharp / sharp.sum()

    # Scale so top crop feels like a real % match (min 60% for top)
    top_idx = np.argmax(sharp)
    if sharp[top_idx] < 0.60:
        boost = 0.60 / sharp[top_idx]
        boost = min(boost, 2.5)
        sharp = np.power(raw_probs, 4 * boost)
        sharp = sharp / sharp.sum()

    classes = label_encoder.classes_

    results = sorted(
        [{'crop': cls, 'percentage': round(prob * 100)}
         for cls, prob in zip(classes, sharp)],
        key=lambda x: x['percentage'],
        reverse=True
    )

    results = [r for r in results if r['percentage'] >= 1]

    for r in results:
        meta = CROP_META.get(r['crop'], {'emoji': '🌿', 'desc': ''})
        r.update(meta)

    return results