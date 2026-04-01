import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'recommendation.csv')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')

def clean_soil(val):
    val = str(val).strip().lower()
    mapping = {
        'loamy':      'Loamy',
        'loam':       'Loamy',
        'fertile':    'Fertile',
        'sandy-loam': 'Sandy-Loam',
        'sandy loam': 'Sandy-Loam',
        'sandy':      'Sandy',
        'clay-loam':  'Clay-Loam',
        'clay loam':  'Clay-Loam',
        'clay':       'Clay',
        'alluvial':   'Alluvial',
        'light':      'Sandy',
        'medium':     'Loamy',
    }
    return mapping.get(val, val.title())

def train():
    print("📂 Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"   Rows: {len(df)}, Columns: {df.columns.tolist()}")

    # ── Clean Soil_type ──────────────────────────────────────────
    print("\n🧹 Cleaning Soil_type...")
    df['Soil_type'] = df['Soil_type'].apply(clean_soil)
    print("   Unique soil types after cleaning:")
    print("  ", df['Soil_type'].value_counts().to_dict())

    # ── Encode Soil_type ─────────────────────────────────────────
    soil_encoder = LabelEncoder()
    df['Soil_encoded'] = soil_encoder.fit_transform(df['Soil_type'])

    # ── Features & Target ────────────────────────────────────────
    X = df[['Temperature', 'Rainfall', 'Altitude', 'Soil_encoded', 'Soil_pH']]
    y = df['label']

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print(f"\n🌾 Crops in model: {list(label_encoder.classes_)}")

    # ── Scale ────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Train / Test split ───────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # ── Train model ──────────────────────────────────────────────
    print("\n🤖 Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n✅ Accuracy: {accuracy * 100:.2f}%")
    print("\n📊 Per-crop performance:")
    print(classification_report(y_test, y_pred,
          target_names=label_encoder.classes_))

    # ── Save ─────────────────────────────────────────────────────
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model,         os.path.join(MODEL_DIR, 'crop_model.pkl'))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    joblib.dump(soil_encoder,  os.path.join(MODEL_DIR, 'soil_encoder.pkl'))
    joblib.dump(scaler,        os.path.join(MODEL_DIR, 'scaler.pkl'))

    print("\n💾 Model saved to app/ml/model/")
    print("   Files: crop_model.pkl, label_encoder.pkl, soil_encoder.pkl, scaler.pkl")

if __name__ == '__main__':
    train()