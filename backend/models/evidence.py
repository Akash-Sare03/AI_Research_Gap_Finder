from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

class EvidenceType(str, Enum):
    EXPLICIT = "explicit"          # Directly stated in paper
    INFERRED = "inferred"           # System reasoned from evidence
    CALCULATED = "calculated"       # Mathematical/statistical derivation
    EXTERNAL = "external"           # From web search
    DISCOVERED = "discovered"       # Novel pattern found by system

class Source(BaseModel):
    paper_id: str
    page_number: Optional[int] = None
    chunk_id: Optional[str] = None
    text: str
    section: Optional[str] = None

class Evidence(BaseModel):
    type: EvidenceType
    description: str
    source: Optional[Source] = None
    reasoning: Optional[str] = None
    calculation: Optional[str] = None
    confidence: str  # low/medium/high

class Finding(BaseModel):
    id: str
    title: str
    description: str
    evidence: List[Evidence]
    reasoning_chain: Optional[List[str]] = None
    confidence: str
    category: str  # limitation, gap, insight, improvement

class AnalysisReport(BaseModel):
    paper_id: str
    paper_metadata: Dict[str, Any]
    explicit_limitations: List[Finding]
    inferred_limitations: List[Finding]
    statistical_insights: List[Finding]
    research_gaps: List[Finding]
    novel_discoveries: List[Finding]
    suggested_improvements: List[Finding]
    external_sources: List[Dict[str, str]]
    reasoning_summary: str