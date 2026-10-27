from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timedelta
from app.services.firestore_service import FirestoreService
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/reports", tags=["reports"])

metrics_collection = FirestoreService("infrastructure_metrics")
sensor_readings_collection = FirestoreService("sensor_readings")
alerts_collection = FirestoreService("alerts")
ai_recommendations_collection = FirestoreService("ai_recommendations")

class DailyMetric(BaseModel):
    date: str
    value: float

class AlertCountBySeverity(BaseModel):
    severity: str
    count: int

class InfrastructureReport(BaseModel):
    overall_avg_cpu: float
    overall_avg_ram: float
    overall_avg_storage: float
    overall_avg_network: float
    cpu_trend: List[DailyMetric]
    ram_trend: List[DailyMetric]

class IoTReport(BaseModel):
    overall_avg_temperature: float
    overall_avg_humidity: float
    temperature_trend: List[DailyMetric]
    humidity_trend: List[DailyMetric]

class EnergyReport(BaseModel):
    overall_avg_power: float
    overall_avg_current: float
    power_trend: List[DailyMetric]
    current_trend: List[DailyMetric]

class AlertReport(BaseModel):
    total_alerts: int
    open_alerts: int
    resolved_alerts: int
    by_severity: List[AlertCountBySeverity]
    alerts_over_time: List[DailyMetric]

class AIReport(BaseModel):
    total_recommendations: int
    avg_risk_score: float
    recommendations_by_priority: dict
    risk_score_trend: List[DailyMetric]

def get_date_range_str(range_type: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> Tuple[str, str]:
    now = datetime.utcnow()
    if range_type == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif range_type == "7d":
        start = now - timedelta(days=7)
        end = now
    elif range_type == "30d":
        start = now - timedelta(days=30)
        end = now
    else:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")) if start_date else (now - timedelta(days=30))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else now
        start = start_dt
        end = end_dt
    return start.isoformat(), end.isoformat()

@router.get("/infrastructure", response_model=InfrastructureReport)
def get_infrastructure_report(
    range: Optional[str] = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    start, end = get_date_range_str(range, start_date, end_date)
    # Fetch all and filter locally due to lack of composite indexes for this generic setup
    all_metrics = metrics_collection.list_documents()
    metrics = [m for m in all_metrics if start <= m.get("timestamp", "") <= end]
    
    if not metrics:
        return InfrastructureReport(overall_avg_cpu=0, overall_avg_ram=0, overall_avg_storage=0, overall_avg_network=0, cpu_trend=[], ram_trend=[])
        
    avg_cpu = sum(m.get("cpu_usage", 0) for m in metrics) / len(metrics)
    avg_ram = sum(m.get("memory_usage", 0) for m in metrics) / len(metrics)
    avg_storage = sum(m.get("storage_usage", 0) for m in metrics) / len(metrics)
    avg_net = sum(m.get("network_usage", 0) for m in metrics) / len(metrics)
    
    # daily stats
    daily_stats = {}
    for m in metrics:
        day = m.get("timestamp", "")[:10]
        if day not in daily_stats:
            daily_stats[day] = {"cpu": [], "ram": []}
        daily_stats[day]["cpu"].append(m.get("cpu_usage", 0))
        daily_stats[day]["ram"].append(m.get("memory_usage", 0))
        
    cpu_trend = []
    ram_trend = []
    for day in sorted(daily_stats.keys()):
        cpu_trend.append(DailyMetric(date=day, value=sum(daily_stats[day]["cpu"]) / len(daily_stats[day]["cpu"])))
        ram_trend.append(DailyMetric(date=day, value=sum(daily_stats[day]["ram"]) / len(daily_stats[day]["ram"])))
        
    return InfrastructureReport(
        overall_avg_cpu=avg_cpu,
        overall_avg_ram=avg_ram,
        overall_avg_storage=avg_storage,
        overall_avg_network=avg_net,
        cpu_trend=cpu_trend,
        ram_trend=ram_trend
    )

@router.get("/iot", response_model=IoTReport)
def get_iot_report(
    range: Optional[str] = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    start, end = get_date_range_str(range, start_date, end_date)
    all_readings = sensor_readings_collection.list_documents()
    readings = [r for r in all_readings if start <= r.get("timestamp", "") <= end]
    
    if not readings:
        return IoTReport(overall_avg_temperature=0, overall_avg_humidity=0, temperature_trend=[], humidity_trend=[])
        
    temps = [r.get("temperature", 0) for r in readings if r.get("temperature") is not None]
    hums = [r.get("humidity", 0) for r in readings if r.get("humidity") is not None]
    
    avg_temp = sum(temps) / len(temps) if temps else 0
    avg_hum = sum(hums) / len(hums) if hums else 0
    
    daily_stats = {}
    for r in readings:
        day = r.get("timestamp", "")[:10]
        if day not in daily_stats:
            daily_stats[day] = {"temp": [], "hum": []}
        if r.get("temperature") is not None: daily_stats[day]["temp"].append(r.get("temperature"))
        if r.get("humidity") is not None: daily_stats[day]["hum"].append(r.get("humidity"))
        
    temp_trend = []
    hum_trend = []
    for day in sorted(daily_stats.keys()):
        if daily_stats[day]["temp"]:
            temp_trend.append(DailyMetric(date=day, value=sum(daily_stats[day]["temp"]) / len(daily_stats[day]["temp"])))
        if daily_stats[day]["hum"]:
            hum_trend.append(DailyMetric(date=day, value=sum(daily_stats[day]["hum"]) / len(daily_stats[day]["hum"])))
            
    return IoTReport(
        overall_avg_temperature=avg_temp,
        overall_avg_humidity=avg_hum,
        temperature_trend=temp_trend,
        humidity_trend=hum_trend
    )

@router.get("/energy", response_model=EnergyReport)
def get_energy_report(
    range: Optional[str] = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    start, end = get_date_range_str(range, start_date, end_date)
    all_readings = sensor_readings_collection.list_documents()
    readings = [r for r in all_readings if start <= r.get("timestamp", "") <= end]
    
    if not readings:
        return EnergyReport(overall_avg_power=0, overall_avg_current=0, power_trend=[], current_trend=[])
        
    powers = [r.get("power", 0) for r in readings if r.get("power") is not None]
    currents = [r.get("current", 0) for r in readings if r.get("current") is not None]
    
    avg_power = sum(powers) / len(powers) if powers else 0
    avg_curr = sum(currents) / len(currents) if currents else 0
    
    daily_stats = {}
    for r in readings:
        day = r.get("timestamp", "")[:10]
        if day not in daily_stats:
            daily_stats[day] = {"power": [], "current": []}
        if r.get("power") is not None: daily_stats[day]["power"].append(r.get("power"))
        if r.get("current") is not None: daily_stats[day]["current"].append(r.get("current"))
        
    pow_trend = []
    curr_trend = []
    for day in sorted(daily_stats.keys()):
        if daily_stats[day]["power"]:
            pow_trend.append(DailyMetric(date=day, value=sum(daily_stats[day]["power"]) / len(daily_stats[day]["power"])))
        if daily_stats[day]["current"]:
            curr_trend.append(DailyMetric(date=day, value=sum(daily_stats[day]["current"]) / len(daily_stats[day]["current"])))
            
    return EnergyReport(
        overall_avg_power=avg_power,
        overall_avg_current=avg_curr,
        power_trend=pow_trend,
        current_trend=curr_trend
    )

@router.get("/alerts", response_model=AlertReport)
def get_alert_report(
    range: Optional[str] = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    start, end = get_date_range_str(range, start_date, end_date)
    all_alerts = alerts_collection.list_documents()
    alerts = [a for a in all_alerts if start <= a.get("created_at", "") <= end]
    
    total = len(alerts)
    open_alerts = len([a for a in alerts if a.get("status", "").upper() == "ACTIVE"])
    resolved_alerts = len([a for a in alerts if a.get("status", "").upper() == "RESOLVED"])
    
    severity_counts = {}
    daily_counts = {}
    
    for a in alerts:
        sev = a.get("severity", "LOW")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        day = a.get("created_at", "")[:10]
        daily_counts[day] = daily_counts.get(day, 0) + 1
        
    by_sev = [AlertCountBySeverity(severity=s, count=c) for s, c in severity_counts.items()]
    alerts_trend = [DailyMetric(date=d, value=float(c)) for d, c in sorted(daily_counts.items())]
    
    return AlertReport(
        total_alerts=total,
        open_alerts=open_alerts,
        resolved_alerts=resolved_alerts,
        by_severity=by_sev,
        alerts_over_time=alerts_trend
    )

@router.get("/ai", response_model=AIReport)
def get_ai_report(
    range: Optional[str] = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    start, end = get_date_range_str(range, start_date, end_date)
    all_recs = ai_recommendations_collection.list_documents()
    recs = [r for r in all_recs if start <= r.get("created_at", "") <= end]
    
    total = len(recs)
    avg_risk = sum(r.get("risk_score", 0) for r in recs) / total if total > 0 else 0
    
    priority_dict = {}
    daily_risk = {}
    
    for r in recs:
        p = r.get("priority", "LOW")
        priority_dict[p] = priority_dict.get(p, 0) + 1
        
        day = r.get("created_at", "")[:10]
        if day not in daily_risk:
            daily_risk[day] = []
        daily_risk[day].append(r.get("risk_score", 0))
        
    risk_trend = [DailyMetric(date=d, value=sum(v)/len(v)) for d, v in sorted(daily_risk.items())]
    
    return AIReport(
        total_recommendations=total,
        avg_risk_score=avg_risk,
        recommendations_by_priority=priority_dict,
        risk_score_trend=risk_trend
    )
