from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from ..models.evidence import Evidence, Finding, Source, EvidenceType

class ReasoningEngine:
    """
    Provides transparent reasoning with full source attribution.
    Every finding includes:
    - What was found
    - Where it came from (page, chunk, text)
    - How it was derived (reasoning chain)
    - Confidence level
    """
    
    def __init__(self):
        self.reasoning_log = []
    
    def create_explicit_finding(self, text: str, paper_id: str, page: int, 
                               chunk_id: str, category: str) -> Finding:
        """Create a finding from explicit text in the paper."""
        
        source = Source(
            paper_id=paper_id,
            page_number=page,
            chunk_id=chunk_id,
            text=text[:200] + "..." if len(text) > 200 else text,
            section=self._detect_section(text)
        )
        
        evidence = Evidence(
            type=EvidenceType.EXPLICIT,
            description=f"Author explicitly states: \"{text[:100]}...\"",
            source=source,
            reasoning="This is directly quoted from the paper",
            confidence="high"
        )
        
        return Finding(
            id=f"{paper_id}_{category}_{datetime.now().timestamp()}",
            title=self._extract_title(text),
            description=text,
            evidence=[evidence],
            reasoning_chain=["1. Identified explicit statement in paper"],
            confidence="high",
            category=category
        )
    
    def create_inferred_finding(self, description: str, paper_id: str, 
                               evidence_text: str, reasoning: str,
                               page: int, chunk_id: str, category: str) -> Finding:
        """Create a finding based on system inference."""
        
        source = Source(
            paper_id=paper_id,
            page_number=page,
            chunk_id=chunk_id,
            text=evidence_text[:200] + "..." if len(evidence_text) > 200 else evidence_text,
            section=self._detect_section(evidence_text)
        )
        
        evidence = Evidence(
            type=EvidenceType.INFERRED,
            description=f"Inferred from evidence: \"{evidence_text[:100]}...\"",
            source=source,
            reasoning=reasoning,
            confidence="medium"
        )
        
        reasoning_chain = [
            f"1. Found evidence in paper: \"{evidence_text[:100]}...\"",
            f"2. Analyzed methodology/dataset limitations",
            f"3. Reasoning: {reasoning}",
            "4. Conclusion: This limitation is likely but not explicitly stated"
        ]
        
        return Finding(
            id=f"{paper_id}_{category}_{datetime.now().timestamp()}",
            title=self._extract_title(description),
            description=description,
            evidence=[evidence],
            reasoning_chain=reasoning_chain,
            confidence="medium",
            category=category
        )
    
    def create_calculated_finding(self, description: str, paper_id: str,
                                 calculation: str, reasoning: str,
                                 metric_values: Dict[str, float],
                                 page: int, chunk_id: str, category: str) -> Finding:
        """Create a finding based on mathematical/statistical calculation."""
        
        source = Source(
            paper_id=paper_id,
            page_number=page,
            chunk_id=chunk_id,
            text=f"Calculated from metrics: {metric_values}",
            section="Statistical Analysis"
        )
        
        evidence = Evidence(
            type=EvidenceType.CALCULATED,
            description=f"Calculated from reported metrics: {metric_values}",
            source=source,
            reasoning=reasoning,
            calculation=calculation,
            confidence="high"
        )
        
        reasoning_chain = [
            f"1. Extracted metrics from paper: {metric_values}",
            f"2. Performed calculation: {calculation}",
            f"3. Result shows: {description}",
            "4. This statistical insight is derived through mathematical reasoning"
        ]
        
        return Finding(
            id=f"{paper_id}_{category}_{datetime.now().timestamp()}",
            title=self._extract_title(description),
            description=description,
            evidence=[evidence],
            reasoning_chain=reasoning_chain,
            confidence="high",
            category=category
        )
    
    def create_external_finding(self, description: str, paper_id: str,
                               external_url: str, external_text: str,
                               reasoning: str, category: str) -> Finding:
        """Create a finding based on external research."""
        
        evidence = Evidence(
            type=EvidenceType.EXTERNAL,
            description=f"External source: {external_text[:100]}...",
            reasoning=f"Found through web search: {reasoning}",
            confidence="medium"
        )
        
        reasoning_chain = [
            f"1. Searched web for related research",
            f"2. Found external source: {external_url[:50]}...",
            f"3. External finding: {external_text[:100]}...",
            f"4. Applied reasoning: {reasoning}",
            "5. This is external evidence, not from the uploaded paper"
        ]
        
        return Finding(
            id=f"{paper_id}_{category}_{datetime.now().timestamp()}",
            title=self._extract_title(description),
            description=description,
            evidence=[evidence],
            reasoning_chain=reasoning_chain,
            confidence="medium",
            category=category
        )
    
    def create_discovered_finding(self, description: str, paper_id: str,
                                 discovery_reasoning: str,
                                 evidence_text: str, page: int,
                                 chunk_id: str, category: str) -> Finding:
        """Create a finding from a novel pattern discovered by the system."""
        
        source = Source(
            paper_id=paper_id,
            page_number=page,
            chunk_id=chunk_id,
            text=evidence_text[:200] + "..." if len(evidence_text) > 200 else evidence_text,
            section="Discovered Pattern"
        )
        
        evidence = Evidence(
            type=EvidenceType.DISCOVERED,
            description=f"Discovered pattern from: \"{evidence_text[:100]}...\"",
            source=source,
            reasoning=discovery_reasoning,
            confidence="medium"
        )
        
        reasoning_chain = [
            f"1. Analyzed paper content: \"{evidence_text[:100]}...\"",
            f"2. Identified non-obvious pattern",
            f"3. Discovery reasoning: {discovery_reasoning}",
            "4. This is a novel insight not explicitly stated in the paper"
        ]
        
        return Finding(
            id=f"{paper_id}_{category}_{datetime.now().timestamp()}",
            title=self._extract_title(description),
            description=description,
            evidence=[evidence],
            reasoning_chain=reasoning_chain,
            confidence="medium",
            category=category
        )
    
    def _detect_section(self, text: str) -> str:
        """Detect which section the text belongs to."""
        text_lower = text.lower()
        if "introduction" in text_lower:
            return "Introduction"
        elif "methodology" in text_lower or "method" in text_lower:
            return "Methodology"
        elif "experiment" in text_lower:
            return "Experiments"
        elif "result" in text_lower:
            return "Results"
        elif "limitation" in text_lower or "future work" in text_lower:
            return "Limitations/Future Work"
        elif "conclusion" in text_lower:
            return "Conclusion"
        else:
            return "General"
    
    def _extract_title(self, text: str) -> str:
        """Extract a short title from text."""
        words = text.split()[:10]
        title = " ".join(words)
        if len(title) > 60:
            title = title[:60] + "..."
        return title
    
    def format_finding(self, finding: Finding) -> str:
        """Format a finding with all reasoning visible."""
        output = []
        output.append(f"## {finding.title}")
        output.append(f"\n**Description:** {finding.description}")
        output.append(f"\n**Category:** {finding.category}")
        output.append(f"\n**Confidence:** {finding.confidence}")
        
        output.append("\n### Evidence:")
        for i, evidence in enumerate(finding.evidence, 1):
            output.append(f"\n**Evidence {i}:**")
            output.append(f"- Type: {evidence.type}")
            output.append(f"- Description: {evidence.description}")
            if evidence.source:
                output.append(f"- Source: Paper '{evidence.source.paper_id}', Page {evidence.source.page_number}")
                output.append(f"- Text: \"{evidence.source.text}\"")
            if evidence.reasoning:
                output.append(f"- Reasoning: {evidence.reasoning}")
            if evidence.calculation:
                output.append(f"- Calculation: {evidence.calculation}")
        
        if finding.reasoning_chain:
            output.append("\n### Reasoning Chain:")
            for step in finding.reasoning_chain:
                output.append(f"- {step}")
        
        return "\n".join(output)