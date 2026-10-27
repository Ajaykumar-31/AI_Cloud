from app.ai.base_agent import BaseAgent, AgentResult
from datetime import datetime, timezone
from dateutil.parser import parse as parse_date

class EnvironmentalAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "EnvironmentalAgent"
        
    def evaluate(self, temperature: float = None, humidity: float = None, timestamp: str = None) -> AgentResult:
        findings = []
        
        if temperature is None or humidity is None:
            findings.append("Environmental data is missing or invalid.")
            return AgentResult(score=0.0, findings=findings, risk_level="UNKNOWN", agent_name=self.name)
            
        if timestamp:
            try:
                dt = parse_date(timestamp)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                if age > 300: # Stale if older than 5 minutes
                    findings.append(f"Environmental data is stale ({(age/60):.1f} minutes old).")
                    return AgentResult(score=0.0, findings=findings, risk_level="UNKNOWN", agent_name=self.name)
            except Exception:
                pass

        risk_level = "LOW"
        temp_score = 100.0
        if temperature < 18 or temperature > 27:
            temp_score -= abs(temperature - 22.5) * 5
            
        hum_score = 100.0
        if humidity < 35 or humidity > 65:
            hum_score -= abs(humidity - 50.0) * 2
            
        overall_score = (temp_score * 0.6) + (hum_score * 0.4)
        
        if temperature > 35 or temperature < 10 or humidity > 85 or humidity < 20:
            risk_level = "CRITICAL"
        elif temperature > 30 or temperature < 15 or humidity > 75 or humidity < 30:
            risk_level = "HIGH"
        elif temperature > 27 or temperature < 18 or humidity > 65 or humidity < 35:
            risk_level = "MEDIUM"
            
        if temperature > 27:
            findings.append(f"Temperature is elevated ({temperature}°C). Cooling required.")
        elif temperature < 18:
            findings.append(f"Temperature is below optimal ({temperature}°C).")
            
        if humidity > 65:
            findings.append(f"High humidity detected ({humidity}%). Risk of condensation.")
        elif humidity < 35:
            findings.append(f"Low humidity detected ({humidity}%). Risk of electrostatic discharge.")
            
        if not findings:
            findings.append("Environmental parameters are optimal.")
            
        return AgentResult(
            score=max(0.0, min(100.0, overall_score)),
            findings=findings,
            risk_level=risk_level,
            agent_name=self.name
        )
