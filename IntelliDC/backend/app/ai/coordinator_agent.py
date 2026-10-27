from typing import List, Dict, Any
from app.ai.base_agent import AgentResult

class CoordinatorAgent:
    def __init__(self):
        self.name = "CoordinatorAgent"
        
    def validate_inputs(self, results: List[AgentResult]) -> bool:
        # Validates that all inputs are indeed AgentResult objects
        if not results:
            return False
        return all(isinstance(r, AgentResult) for r in results)
        
    def compile_decision_input(self, results: List[AgentResult]) -> Dict[str, Any]:
        """
        Receives outputs from all specialized agents, validates them,
        combines them, and prepares the final structured decision input.
        """
        if not self.validate_inputs(results):
            raise ValueError("Invalid agent results provided to Coordinator.")
            
        final_findings = []
        scores = {}
        risk_levels = []
        
        for result in results:
            scores[result.agent_name] = result.score
            final_findings.extend([f"[{result.agent_name}] {finding}" for finding in result.findings])
            risk_levels.append(result.risk_level)
            
        # Determine aggregate risk.
        # Simple rule: If any agent reports CRITICAL, the aggregate is CRITICAL.
        if "UNKNOWN" in risk_levels:
            aggregate_risk = "UNKNOWN"
        elif "CRITICAL" in risk_levels:
            aggregate_risk = "CRITICAL"
        elif "HIGH" in risk_levels:
            aggregate_risk = "HIGH"
        elif "MEDIUM" in risk_levels:
            aggregate_risk = "MEDIUM"
        else:
            aggregate_risk = "LOW"
            
        # Overall health score can be a simple average of the agents.
        # This can be later fed into TOPSIS or another ranking algorithm.
        valid_scores = [s for s in scores.values() if s is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        
        return {
            "coordinator_name": self.name,
            "overall_health_score": round(overall_score, 2),
            "aggregate_risk_level": aggregate_risk,
            "detailed_scores": scores,
            "combined_findings": final_findings,
            "action_required": aggregate_risk in ["HIGH", "CRITICAL"]
        }
