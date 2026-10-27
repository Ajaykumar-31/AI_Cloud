from app.ai.base_agent import BaseAgent, AgentResult

class EnergyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "EnergyAgent"
        
    def evaluate(self, current: float = None, power: float = None) -> AgentResult:
        findings = []
        
        if current is None or power is None or current < 0 or power < 0:
            findings.append("Power consumption measurements are invalid or unavailable. Cannot assess energy efficiency.")
            return AgentResult(score=0.0, findings=findings, risk_level="UNKNOWN", agent_name=self.name)
            
        risk_level = "LOW"
        # Assuming a standard rack limit of 16A and 3500W for thresholds
        CURRENT_MAX = 16.0
        POWER_MAX = 3500.0
        
        current_pct = (current / CURRENT_MAX) * 100
        power_pct = (power / POWER_MAX) * 100
        
        max_pct = max(current_pct, power_pct)
        score = 100.0 - max_pct
        
        if max_pct >= 95.0:
            risk_level = "CRITICAL"
        elif max_pct >= 80.0:
            risk_level = "HIGH"
        elif max_pct >= 60.0:
            risk_level = "MEDIUM"
            
        if current > CURRENT_MAX * 0.9:
            findings.append(f"Current draw is near absolute limits ({current}A).")
        elif current > CURRENT_MAX * 0.75:
            findings.append(f"Elevated current draw ({current}A).")
            
        if power > POWER_MAX * 0.9:
            findings.append(f"Power consumption is critically high ({power}W).")
            
        if not findings:
            findings.append("Energy consumption is within safe limits.")
            
        return AgentResult(
            score=max(0.0, min(100.0, score)),
            findings=findings,
            risk_level=risk_level,
            agent_name=self.name
        )
