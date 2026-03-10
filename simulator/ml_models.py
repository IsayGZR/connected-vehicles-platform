import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pickle
import os

# ===== GENERAR DATOS SINTÉTICOS =====
def generate_training_data(n_samples=3000):
    np.random.seed(42)
    data = []

    for _ in range(n_samples):
        rpm = np.random.uniform(1000, 3500)
        temperature = np.random.uniform(75, 95)
        distance = np.random.uniform(0, 50000)
        brake_events = np.random.randint(0, 5)
        avg_speed = np.random.uniform(30, 80)
        needs_maintenance = 0

        if np.random.random() > 0.55:
            rpm = np.random.uniform(3500, 6000)
            temperature = np.random.uniform(95, 115)
            distance = np.random.uniform(40000, 150000)
            brake_events = np.random.randint(5, 20)
            avg_speed = np.random.uniform(80, 140)
            needs_maintenance = 1

        data.append({
            "rpm": rpm,
            "temperature": temperature,
            "distance": distance,
            "brake_events": brake_events,
            "avg_speed": avg_speed,
            "needs_maintenance": needs_maintenance
        })

    return pd.DataFrame(data)

# ===== ENTRENAR MODELOS =====
def train_models():
    print("🤖 Entrenando modelos ML...")

    df = generate_training_data()
    features = ["rpm", "temperature", "distance", "brake_events", "avg_speed"]
    X = df[features].values
    y = df["needs_maintenance"].values

    # Scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 1. Random Forest — Mantenimiento predictivo
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_scaled, y)
    print("✅ Random Forest entrenado")

    # 2. Isolation Forest — Detección de anomalías
    normal_data = X_scaled[y == 0]
    iso_model = IsolationForest(contamination=0.1, random_state=42)
    iso_model.fit(normal_data)
    print("✅ Isolation Forest entrenado")

    # 3. Regresión Lineal — Predicción de falla de motor
    # Genera datos: temperatura + RPM → km hasta sobrecalentamiento
    temps = np.random.uniform(75, 115, 2000)
    rpms = np.random.uniform(1000, 6000, 2000)
    km_to_failure = np.maximum(0, 500 - (temps - 75) * 8 - (rpms - 1000) * 0.05 + np.random.normal(0, 20, 2000))
    X_reg = np.column_stack([temps, rpms])
    reg_model = LinearRegression()
    reg_model.fit(X_reg, km_to_failure)
    print("✅ Regresión Lineal entrenada")

    # Guardar modelos
    os.makedirs("models", exist_ok=True)
    pickle.dump(rf_model, open("models/rf_model.pkl", "wb"))
    pickle.dump(iso_model, open("models/iso_model.pkl", "wb"))
    pickle.dump(reg_model, open("models/reg_model.pkl", "wb"))
    pickle.dump(scaler, open("models/scaler.pkl", "wb"))
    print("✅ Modelos guardados en /models")

# ===== PREDICCIONES =====
class MLPredictor:
    def __init__(self):
        self.rf_model = pickle.load(open("models/rf_model.pkl", "rb"))
        self.iso_model = pickle.load(open("models/iso_model.pkl", "rb"))
        self.reg_model = pickle.load(open("models/reg_model.pkl", "rb"))
        self.scaler = pickle.load(open("models/scaler.pkl", "rb"))

    def predict(self, rpm, temperature, distance, brake_events, avg_speed):
        features = np.array([[rpm, temperature, distance, brake_events, avg_speed]])
        features_scaled = self.scaler.transform(features)

        # 1. Mantenimiento predictivo (Random Forest)
        maintenance_prob = self.rf_model.predict_proba(features_scaled)[0][1] * 100

        # 2. Detección de anomalías (Isolation Forest)
        anomaly_score = self.iso_model.decision_function(features_scaled)[0]
        is_anomaly = self.iso_model.predict(features_scaled)[0] == -1
        anomaly_prob = max(0, min(100, (0.1 - anomaly_score) * 500))

        # 3. Predicción de falla de motor (Regresión)
        km_to_failure = max(0, self.reg_model.predict([[temperature, rpm]])[0])

        return {
            "maintenance_prob": round(maintenance_prob, 1),
            "is_anomaly": bool(is_anomaly),
            "anomaly_prob": round(anomaly_prob, 1),
            "km_to_failure": round(km_to_failure, 1)
        }

if __name__ == "__main__":
    train_models()
    print("\n🧪 Probando predicciones...")
    predictor = MLPredictor()

    # Vehículo normal
    result = predictor.predict(rpm=2000, temperature=85, distance=10000, brake_events=2, avg_speed=60)
    print(f"Vehículo normal: {result}")

    # Vehículo con problemas
    result = predictor.predict(rpm=5500, temperature=110, distance=90000, brake_events=15, avg_speed=120)
    print(f"Vehículo con problemas: {result}")