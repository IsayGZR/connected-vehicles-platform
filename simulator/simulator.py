import asyncio
import json
import random
from datetime import datetime
#from azure.iot.device.aio import IoTHubDeviceClient
from azure.cosmos import CosmosClient
import uuid
from dotenv import load_dotenv
import os
load_dotenv()

from ml_models import MLPredictor

# Inicializar predictor ML
ml_predictor = MLPredictor()

# ===== CONFIGURACIÓN =====
COSMOS_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
COSMOS_DATABASE = "VehicleDB"
COSMOS_CONTAINER = "TelemetryData"


ROUTES = [
    {"name": "Reforma", "points": [(19.4270, -99.1676), (19.4269, -99.1650), (19.4268, -99.1620), (19.4267, -99.1590), (19.4266, -99.1560), (19.4265, -99.1530)]},
    {"name": "Insurgentes", "points": [(19.4180, -99.1676), (19.4200, -99.1670), (19.4220, -99.1665), (19.4240, -99.1660), (19.4260, -99.1655), (19.4280, -99.1650)]},
    {"name": "Periférico", "points": [(19.3800, -99.1900), (19.3850, -99.1850), (19.3900, -99.1800), (19.3950, -99.1750), (19.4000, -99.1700), (19.4050, -99.1650)]},
    {"name": "Viaducto", "points": [(19.4000, -99.1500), (19.4010, -99.1550), (19.4020, -99.1600), (19.4030, -99.1650), (19.4040, -99.1700), (19.4050, -99.1750)]},
    {"name": "Observatorio", "points": [(19.4050, -99.2000), (19.4060, -99.1950), (19.4070, -99.1900), (19.4080, -99.1850), (19.4090, -99.1800), (19.4100, -99.1750)]},
    {"name": "Tlalpan", "points": [(19.3500, -99.1600), (19.3550, -99.1580), (19.3600, -99.1560), (19.3650, -99.1540), (19.3700, -99.1520), (19.3750, -99.1500)]},
    {"name": "Polanco", "points": [(19.4320, -99.1950), (19.4330, -99.1920), (19.4340, -99.1890), (19.4350, -99.1860), (19.4360, -99.1830), (19.4370, -99.1800)]},
    {"name": "Coyoacán", "points": [(19.3500, -99.1620), (19.3480, -99.1600), (19.3460, -99.1580), (19.3440, -99.1560), (19.3420, -99.1540), (19.3400, -99.1520)]},
    {"name": "Santa Fe", "points": [(19.3600, -99.2600), (19.3620, -99.2560), (19.3640, -99.2520), (19.3660, -99.2480), (19.3680, -99.2440), (19.3700, -99.2400)]},
    {"name": "Xochimilco", "points": [(19.2570, -99.1050), (19.2600, -99.1080), (19.2630, -99.1110), (19.2660, -99.1140), (19.2690, -99.1170), (19.2720, -99.1200)]},
]

VEHICLES = [
    {"id": "VH001", "model": "Tesla Model 3"},
    {"id": "VH002", "model": "Ford F-150"},
    {"id": "VH003", "model": "Toyota Camry"},
    {"id": "VH004", "model": "BMW X5"},
    {"id": "VH005", "model": "Nissan Sentra"},
    {"id": "VH006", "model": "Chevrolet Silverado"},
    {"id": "VH007", "model": "Honda Civic"},
    {"id": "VH008", "model": "Volkswagen Jetta"},
    {"id": "VH009", "model": "Mazda CX-5"},
    {"id": "VH010", "model": "Hyundai Tucson"},
]

# ===== CLIENTE COSMOS =====
cosmos_client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
database = cosmos_client.get_database_client(COSMOS_DATABASE)
container = database.get_container_client(COSMOS_CONTAINER)

# ===== ANÁLISIS ML =====
def analyze_vehicle(speed, rpm, acceleration, brake_force, temperature, fuel, history, distance, total_brake_events):
    risk_score = 0
    alerts = []

    if speed > 100:
        risk_score += 40
        alerts.append("EXCESO DE VELOCIDAD")
    elif speed > 80:
        risk_score += 20
        alerts.append("VELOCIDAD ALTA")
    if brake_force > 80:
        risk_score += 30
        alerts.append("FRENADA BRUSCA")
    if acceleration > 15:
        risk_score += 20
        alerts.append("ACELERACIÓN BRUSCA")
    if rpm > 4000:
        risk_score += 10
        alerts.append("RPM ALTO")
    if temperature > 105:
        risk_score += 15
        alerts.append("TEMPERATURA CRÍTICA")
    if fuel < 10:
        risk_score += 10
        alerts.append("COMBUSTIBLE BAJO")

    incident_probability = 0
    if len(history) >= 3:
        avg_risk = sum(history[-3:]) / 3
        trend = history[-1] - history[0] if len(history) > 1 else 0
        incident_probability = min(100, avg_risk + (trend * 2))

    # ML Predictions
    avg_speed = sum(history) / len(history) if history else speed
    ml = ml_predictor.predict(
        rpm=rpm,
        temperature=temperature,
        distance=distance,
        brake_events=total_brake_events,
        avg_speed=avg_speed
    )

    if ml["is_anomaly"]:
        alerts.append("ANOMALÍA DETECTADA")

    fuel_km_remaining = round((fuel / 100) * 450, 1)

    if risk_score >= 60:
        status = "PELIGRO"
    elif risk_score >= 30:
        status = "PRECAUCIÓN"
    else:
        status = "NORMAL"

    return {
        "status": status,
        "risk_score": risk_score,
        "alerts": alerts,
        "incident_probability": round(incident_probability, 1),
        "fuel_km_remaining": fuel_km_remaining,
        "maintenance_prob": ml["maintenance_prob"],
        "is_anomaly": ml["is_anomaly"],
        "anomaly_prob": ml["anomaly_prob"],
        "km_to_failure": ml["km_to_failure"]
    }

# ===== SIMULADOR =====
class VehicleSimulator:
    def __init__(self, vehicle, route):
        self.vehicle = vehicle
        self.route = route
        self.point_index = 0
        self.speed = random.uniform(40, 70)
        self.rpm = random.uniform(1500, 3000)
        self.temperature = random.uniform(80, 95)
        self.fuel = random.uniform(30, 100)
        self.risk_history = []
        self.total_incidents = 0
        self.distance = 0
        self.total_brake_events = 0

    def generate_telemetry(self):
        points = self.route["points"]
        current = points[self.point_index % len(points)]
        lat = current[0] + random.uniform(-0.0005, 0.0005)
        lng = current[1] + random.uniform(-0.0005, 0.0005)

        event_chance = random.random()
        if event_chance > 0.85:
            self.speed = random.uniform(100, 140)
            brake_force = random.uniform(70, 100)
            acceleration = random.uniform(10, 20)
        else:
            self.speed = random.uniform(20, 85)
            brake_force = random.uniform(0, 30)
            acceleration = random.uniform(0, 8)

        self.rpm = self.speed * 40 + random.uniform(-200, 200)
        self.temperature += random.uniform(-0.5, 1.0)
        self.temperature = max(75, min(115, self.temperature))
        self.fuel -= random.uniform(0.01, 0.05)
        self.fuel = max(0, self.fuel)
        self.distance += self.speed * (1/3600)

        if brake_force > 80:
            self.total_brake_events += 1

        analysis = analyze_vehicle(
            self.speed, self.rpm, acceleration, brake_force,
            self.temperature, self.fuel, self.risk_history,
            self.distance, self.total_brake_events
        )

        self.risk_history.append(analysis["risk_score"])
        if len(self.risk_history) > 10:
            self.risk_history.pop(0)
        if analysis["status"] == "PELIGRO":
            self.total_incidents += 1

        telemetry = {
            "id": str(uuid.uuid4()),
            "vehiclesID": self.vehicle["id"],
            "model": self.vehicle["model"],
            "route": self.route["name"],
            "latitude": lat,
            "longitude": lng,
            "speed": round(self.speed, 1),
            "rpm": round(self.rpm, 0),
            "temperature": round(self.temperature, 1),
            "fuel": round(self.fuel, 1),
            "brake_force": round(brake_force, 1),
            "acceleration": round(acceleration, 1),
            "status": analysis["status"],
            "risk_score": analysis["risk_score"],
            "alerts": analysis["alerts"],
            "incident_probability": analysis["incident_probability"],
            "fuel_km_remaining": analysis["fuel_km_remaining"],
            "total_incidents": self.total_incidents,
            "maintenance_prob": analysis["maintenance_prob"],
            "is_anomaly": analysis["is_anomaly"],
            "anomaly_prob": analysis["anomaly_prob"],
            "km_to_failure": analysis["km_to_failure"],
            "distance": round(self.distance, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        self.point_index += 1
        return telemetry

'''# ===== ENVIAR A IOT HUB + COSMOS =====
async def send_telemetry(simulator):
    vehicle_id = simulator.vehicle["id"]
    conn_str = DEVICE_CONNECTION_STRINGS[vehicle_id]

    # Conectar al IoT Hub como dispositivo real
    iot_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await iot_client.connect()
    print(f"🔌 {vehicle_id} conectado al IoT Hub")

    while True:
        telemetry = simulator.generate_telemetry()

        # Enviar a IoT Hub
        try:
            message = json.dumps(telemetry)
            await iot_client.send_message(message)
        except Exception as e:
            pass  # Continuar aunque IoT Hub falle

        # Guardar en Cosmos DB
        try:
            container.upsert_item(telemetry)
            print(f"✅ {vehicle_id} | IoT Hub ✓ | {telemetry['status']} | {telemetry['speed']} km/h | Combustible: {telemetry['fuel_km_remaining']} km restantes")
        except Exception as e:
            print(f"❌ Error Cosmos {vehicle_id}: {e}")

        await asyncio.sleep(1)'''
        
async def send_telemetry(simulator):
    vehicle_id = simulator.vehicle["id"]
    print(f"🚗 {vehicle_id} iniciado")

    while True:
        telemetry = simulator.generate_telemetry()
        try:
            container.upsert_item(telemetry)
            print(f"✅ {vehicle_id} | {telemetry['status']} | {telemetry['speed']} km/h | Mant: {telemetry['maintenance_prob']}% | Anomalía: {telemetry['is_anomaly']}")
        except Exception as e:
            print(f"❌ Error {vehicle_id}: {e}")
        await asyncio.sleep(1)

# ===== MAIN =====
async def main():
    print("🚗 Iniciando Connected Vehicle Platform con Azure IoT Hub...")
    simulators = [
        VehicleSimulator(VEHICLES[i], ROUTES[i % len(ROUTES)]) for i in range(10)
    ]
    tasks = [send_telemetry(sim) for sim in simulators]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())