from typing import Optional
from app.services.firestore_service import FirestoreService
from datetime import datetime

alerts_collection = FirestoreService("alerts")

# Configurable Thresholds
THRESHOLDS = {
    "infrastructure": {
        "cpu": {"CRITICAL": 90.0, "HIGH": 75.0, "MEDIUM": 60.0},
        "ram": {"CRITICAL": 90.0, "HIGH": 75.0, "MEDIUM": 60.0},
        "storage": {"CRITICAL": 90.0, "HIGH": 80.0, "MEDIUM": 70.0},
        "network": {"CRITICAL": 90.0, "HIGH": 75.0, "MEDIUM": 60.0},
    },
    "iot": {
        "temperature": {"CRITICAL": 35.0, "HIGH": 30.0, "MEDIUM": 27.0},
        "humidity": {"CRITICAL": 85.0, "HIGH": 75.0, "MEDIUM": 65.0},
        "power": {"CRITICAL": 3000.0, "HIGH": 2500.0, "MEDIUM": 2000.0},
    }
}

def determine_severity(metric_name: str, value: float, category: str) -> Optional[str]:
    thresholds = THRESHOLDS.get(category, {}).get(metric_name)
    if not thresholds:
        return None
    
    if value >= thresholds["CRITICAL"]:
        return "CRITICAL"
    elif value >= thresholds["HIGH"]:
        return "HIGH"
    elif value >= thresholds["MEDIUM"]:
        return "MEDIUM"
    return None

def check_and_create_alert(category: str, source: str, metric_name: str, value: float, server_id: str = None, device_id: str = None):
    severity = determine_severity(metric_name, value, category)
    if not severity:
        return
        
    thresholds = THRESHOLDS.get(category, {}).get(metric_name)
    threshold_value = thresholds[severity]
    
    # Check for existing active alert for this metric and entity
    all_alerts = alerts_collection.list_documents()
    for alert in all_alerts:
        if alert.get("source") == source and alert.get("metric") == metric_name:
            st = alert.get("status", "").upper()
            if st in ["ACTIVE", "ACKNOWLEDGED"]:
                if server_id and alert.get("server_id") == server_id:
                    return
                if device_id and alert.get("device_id") == device_id:
                    return
        
    # Create new alert
    new_alert = {
        "severity": severity,
        "source": source,
        "metric": metric_name,
        "server_id": server_id,
        "device_id": device_id,
        "value": value,
        "threshold": threshold_value,
        "message": f"{metric_name.upper()} reached {value}, crossing the {severity} threshold of {threshold_value}.",
        "status": "ACTIVE",
        "created_at": datetime.utcnow().isoformat()
    }
    alerts_collection.create_document(data=new_alert)

def evaluate_infrastructure_metrics(server_id: str, cpu: float, ram: float, storage: float, network: float):
    metrics = {"cpu": cpu, "ram": ram, "storage": storage, "network": network}
    for metric_name, value in metrics.items():
        if value is not None:
            check_and_create_alert("infrastructure", "InfrastructureMonitoring", metric_name, value, server_id=server_id)

def evaluate_iot_readings(device_id: str, temperature: float, humidity: float, power: float):
    metrics = {"temperature": temperature, "humidity": humidity, "power": power}
    for metric_name, value in metrics.items():
        if value is not None:
            check_and_create_alert("iot", "IoTSensor", metric_name, value, device_id=device_id)
