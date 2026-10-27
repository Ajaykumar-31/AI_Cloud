from pydantic import BaseModel
from typing import List, Optional
from abc import ABC, abstractmethod

class AgentResult(BaseModel):
    score: float  # Normalized score usually between 0.0 and 100.0
    findings: List[str]
    risk_level: str  # e.g., "LOW", "MEDIUM", "HIGH", "CRITICAL"
    agent_name: str

class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def evaluate(self, *args, **kwargs) -> AgentResult:
        pass
