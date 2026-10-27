from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DailyMetric(BaseModel):
    date: str
    value: float

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

class AlertCountBySeverity(BaseModel):
    severity: str
    count: int

class AlertReport(BaseModel):
    total_alerts: int
    open_alerts: int
    resolved_alerts: int
    by_severity: List[AlertCountBySeverity]
    alerts_over_time: List[DailyMetric]

class AIReport(BaseModel):
    total_recommendations: int
    avg_risk_score: float
    recommendations_by_priority: Dict[str, int]
    risk_score_trend: List[DailyMetric]
