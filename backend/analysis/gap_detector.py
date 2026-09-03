from typing import List, Dict, Any, Optional
import json
from ..core.llm import LLMService

class GapDetector:
    """Detect research gaps across papers."""
    
    def __init__(self):
        self.llm = LLMService()
        
        self.gap_categories = [
            "Dataset Gap",
            "Methodological Gap",
            "Evaluation Gap",
            "Generalization Gap",
            "Domain Gap",
            "Geographic Gap",
            "Language Gap",
            "Temporal Gap",
            "Scalability Gap",
            "Reproducibility Gap",
            "Real-world Deployment Gap",
            "Benchmarking Gap"
        ]
    
    def detect_gaps(self, papers_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect research gaps from paper analysis."""
        if not papers_analysis:
            return []
        
        prompt = self._build_gap_prompt(papers_analysis)
        
        try:
            response = self.llm.generate(prompt, temperature=0.2)
            gaps = self._parse_gap_response(response)
            
            # Add evidence and citations
            for gap in gaps:
                gap["evidence"] = self._find_evidence(gap, papers_analysis)
                gap["confidence"] = self._assess_confidence(gap, papers_analysis)
            
            return gaps
        except Exception as e:
            print(f"Error detecting gaps: {e}")
            return []
    
    def _build_gap_prompt(self, papers_analysis: List[Dict[str, Any]]) -> str:
        """Build prompt for gap detection."""
        prompt = """You are an AI research analyst analyzing multiple research papers to identify research gaps.

        ## Paper Analyses:
        """
        
        for analysis in papers_analysis:
            prompt += f"""
            Paper: {analysis.get('paper_id', 'Unknown')}
            Explicit Limitations: {analysis.get('explicit_limitations', [])}
            Inferred Limitations: {analysis.get('inferred_limitations', [])}
            Methodology: {analysis.get('methodology', 'Not specified')}
            Dataset: {analysis.get('dataset', 'Not specified')}
            """
        
        prompt += """
        ## Task:
        Identify potential research gaps based on the analysis.

        ## Gap Categories:
        1. Dataset Gap - Limitations in dataset size, diversity, or representativeness
        2. Methodological Gap - Limitations in methods or approaches used
        3. Evaluation Gap - Limitations in how methods are evaluated
        4. Generalization Gap - How well methods generalize to new scenarios
        5. Domain Gap - Missing domain applications
        6. Geographic Gap - Geographic limitations
        7. Language Gap - Language limitations
        8. Temporal Gap - Using outdated data or methods
        9. Scalability Gap - How well methods scale
        10. Reproducibility Gap - Issues with reproducibility
        11. Real-world Deployment Gap - Gap between research and practice
        12. Benchmarking Gap - Need for better benchmarks

        For each gap provide:
        - Category: [category]
        - Description: [description]
        - Evidence: [what evidence supports this]
        - Reasoning: [your reasoning]
        - Confidence: [low/medium/high]
        - Potential Research Direction: [suggestion]

        Format each gap as:
        GAP: [description]
        CATEGORY: [category]
        REASONING: [reasoning]
        CONFIDENCE: [confidence]
        DIRECTION: [suggestion]
        """
        
        return prompt
    
    def _parse_gap_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured gaps."""
        gaps = []
        lines = response.strip().split('\n')
        
        current_gap = {}
        for line in lines:
            if line.startswith('GAP:'):
                if current_gap:
                    gaps.append(current_gap)
                current_gap = {'description': line.replace('GAP:', '').strip()}
            elif line.startswith('CATEGORY:'):
                if current_gap:
                    current_gap['category'] = line.replace('CATEGORY:', '').strip()
            elif line.startswith('REASONING:'):
                if current_gap:
                    current_gap['reasoning'] = line.replace('REASONING:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                if current_gap:
                    current_gap['confidence'] = line.replace('CONFIDENCE:', '').strip().lower()
            elif line.startswith('DIRECTION:'):
                if current_gap:
                    current_gap['potential_direction'] = line.replace('DIRECTION:', '').strip()
        
        if current_gap:
            gaps.append(current_gap)
        
        return gaps
    
    def _find_evidence(self, gap: Dict[str, Any], papers_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find supporting evidence for a gap."""
        evidence = []
        for analysis in papers_analysis:
            # Check explicit limitations
            for limitation in analysis.get('explicit_limitations', []):
                if any(word in limitation.get('text', '').lower() for word in gap.get('description', '').lower().split()[:3]):
                    evidence.append({
                        "paper_id": analysis.get('paper_id', 'unknown'),
                        "type": "explicit",
                        "text": limitation.get('text', '')
                    })
            
            # Check inferred limitations
            for limitation in analysis.get('inferred_limitations', []):
                if any(word in limitation.get('text', '').lower() for word in gap.get('description', '').lower().split()[:3]):
                    evidence.append({
                        "paper_id": analysis.get('paper_id', 'unknown'),
                        "type": "inferred",
                        "text": limitation.get('text', '')
                    })
        
        return evidence[:3]  # Return top 3 evidence
    
    def _assess_confidence(self, gap: Dict[str, Any], papers_analysis: List[Dict[str, Any]]) -> str:
        """Assess confidence level for a gap."""
        # If confidence is already set, use it
        if 'confidence' in gap and gap['confidence']:
            return gap['confidence']
        
        # Otherwise assess based on evidence
        evidence = self._find_evidence(gap, papers_analysis)
        if len(evidence) >= 3:
            return "high"
        elif len(evidence) >= 1:
            return "medium"
        else:
            return "low"