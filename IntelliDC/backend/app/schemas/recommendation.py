from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Optional overrides when triggering an analysis."""
    pass  # Currently uses live DB data; extensible for future overrides


class AgentScoreDetail(BaseModel):
    agent_name: str
    score: float
    risk_level: str
    findings: List[str]


class RecommendationResponse(BaseModel):
    id: int
    server_id: int
    server_name: Optional[str] = None
    risk_score: float
    priority: str
    agent_scores: List[AgentScoreDetail]
    reasons: List[str]
    topsis_rank: Optional[int] = None
    recommendation: str
    explanation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationSummary(BaseModel):
    id: int
    server_id: int
    server_name: Optional[str] = None
    risk_score: float
    priority: str
    topsis_rank: Optional[int] = None
    recommendation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
