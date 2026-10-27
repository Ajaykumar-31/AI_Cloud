from app.ai.base_agent import BaseAgent, AgentResult

class InfrastructureAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "InfrastructureAgent"
        
    def evaluate(self, cpu: float = None, ram: float = None, storage: float = None, network: float = None) -> AgentResult:
        findings = []
        risk_level = "LOW"
        
        if cpu is None or ram is None or storage is None:
            findings.append("Missing essential infrastructure metrics (CPU, RAM, or Storage).")
            return AgentResult(score=0.0, findings=findings, risk_level="UNKNOWN", agent_name=self.name)
        
        # Calculate raw health score (100 is best, 0 is worst)
        # Using a weighted average favoring CPU and RAM
        health_score = 100.0 - (0.4 * cpu + 0.4 * ram + 0.1 * storage + 0.1 * (network or 0))
        
        max_utilization = max(cpu, ram, storage, (network or 0))
        
        if max_utilization >= 90.0:
            risk_level = "CRITICAL"
        elif max_utilization >= 75.0:
            risk_level = "HIGH"
        elif max_utilization > 50.0: # Only if strictly greater than 50
            risk_level = "MEDIUM"
            
        if cpu > 85.0:
            findings.append(f"CPU utilization is high ({cpu}%)")
        if ram > 85.0:
            findings.append(f"RAM utilization is high ({ram}%)")
        if storage > 90.0:
            findings.append(f"Storage is nearing capacity ({storage}%)")
        if network is not None and network > 80.0:
            findings.append(f"Network bandwidth is saturated ({network}%)")
            
        if not findings:
            findings.append("Infrastructure metrics are within normal operating parameters.")
            
        return AgentResult(
            score=max(0.0, min(100.0, health_score)),
            findings=findings,
            risk_level=risk_level,
            agent_name=self.name
        )
