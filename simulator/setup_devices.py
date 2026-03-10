from azure.iot.hub import IoTHubRegistryManager
from dotenv import load_dotenv
import os
load_dotenv()

CONNECTION_STRING = os.getenv("IOT_CONNECTION_STRING")

VEHICLES = ["VH001", "VH002", "VH003", "VH004", "VH005",
            "VH006", "VH007", "VH008", "VH009", "VH010"]

registry = IoTHubRegistryManager(CONNECTION_STRING)

for vehicle_id in VEHICLES:
    try:
        device = registry.create_device_with_sas(
            device_id=vehicle_id,
            primary_key=None,
            secondary_key=None,
            status="enabled"
        )
        print(f"✅ Dispositivo creado: {vehicle_id}")
    except Exception as e:
        if "DeviceAlreadyExists" in str(e):
            print(f"⚠️ Ya existe: {vehicle_id}")
        else:
            print(f"❌ Error {vehicle_id}: {e}")

print("✅ Listo!")