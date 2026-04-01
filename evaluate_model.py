from app.ml.predict import load_models
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Load dataset and model
df = pd.read_csv('data/recommendation.csv')
model, label_encoder, soil_encoder, scaler = load_models()

# Encode labels
df['Soil_encoded'] = soil_encoder.transform(df['Soil_type'].map(lambda x: x.title()))
y_encoded = label_encoder.transform(df['label'])
X = df[['Temperature','Rainfall','Altitude','Soil_encoded','Soil_pH']]
X_scaled = scaler.transform(X)

# Split for evaluation
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# Predictions
y_pred = model.predict(X_test)
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()