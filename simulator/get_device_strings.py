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
        device = registry.get_device(vehicle_id)
        key = device.authentication.symmetric_key.primary_key
        conn_str = f"HostName=connected-vehicles-hub.azure-devices.net;DeviceId={vehicle_id};SharedAccessKey={key}"
        print(f'"{vehicle_id}": "{conn_str}",')
    except Exception as e:
        print(f"❌ Error {vehicle_id}: {e}")