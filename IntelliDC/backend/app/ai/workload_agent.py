from app.ai.base_agent import BaseAgent, AgentResult

class WorkloadContextAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "WorkloadContextAgent"
        
    def evaluate(self, priority: str, criticality: str, sensitivity: str) -> AgentResult:
        findings = []
        
        weight_map = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
            "PUBLIC": 1,
            "INTERNAL": 2,
            "CONFIDENTIAL": 3,
            "RESTRICTED": 4
        }
        
        p_val = weight_map.get(priority.upper(), 1)
        c_val = weight_map.get(criticality.upper(), 1)
        s_val = weight_map.get(sensitivity.upper(), 1)
        
        # Calculate a combined workload importance score (higher score = more critical workload)
        # Max score is 12. Normalizing to 100.
        raw_score = p_val + c_val + s_val
        score = (raw_score / 12.0) * 100.0
        
        # Determine risk level based on the importance of the workload.
        # A critical workload implies a CRITICAL risk if the server fails.
        if p_val == 4 or c_val == 4:
            risk_level = "CRITICAL"
        elif p_val == 3 or c_val == 3 or s_val == 4:
            risk_level = "HIGH"
        elif raw_score >= 6:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        if p_val >= 3:
            findings.append(f"Workload Priority is {priority}.")
        if c_val >= 3:
            findings.append(f"Workload Criticality is {criticality}. Ensure high availability.")
        if s_val >= 3:
            findings.append(f"Data Sensitivity is {sensitivity}. Security constraints must be met.")
            
        if not findings:
            findings.append("Workload is standard priority and non-critical.")
            
        return AgentResult(
            score=max(0.0, min(100.0, score)),
            findings=findings,
            risk_level=risk_level,
            agent_name=self.name
        )
