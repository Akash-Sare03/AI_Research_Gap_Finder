from typing import List, Dict, Any, Optional
import re
from ..core.llm import LLMService

class LimitationDetector:
    """Detect limitations in research papers."""
    
    def __init__(self):
        self.llm = LLMService()
        
        # Keywords for explicit limitation detection
        self.explicit_keywords = [
            "limitation", "limitations", "shortcoming", "drawback", 
            "weakness", "disadvantage", "we acknowledge", "future work",
            "future research", "however", "but", "although"
        ]
    
    def detect_explicit_limitations(self, text: str) -> List[Dict[str, Any]]:
        """Detect explicitly stated limitations."""
        limitations = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_lower = sentence.strip().lower()
            if any(keyword in sentence_lower for keyword in self.explicit_keywords):
                # Check if it's actually discussing a limitation
                if "limitation" in sentence_lower or "future work" in sentence_lower:
                    limitations.append({
                        "text": sentence.strip(),
                        "type": "explicit",
                        "confidence": "high"
                    })
        
        return limitations
    
    def analyze_paper(self, paper_text: str, paper_id: str) -> Dict[str, Any]:
        """Analyze a paper for limitations."""
        explicit = self.detect_explicit_limitations(paper_text)
        
        # Use LLM to infer potential limitations
        inferred = self._infer_limitations(paper_text, paper_id)
        
        return {
            "paper_id": paper_id,
            "explicit_limitations": explicit,
            "inferred_limitations": inferred,
            "total_explicit": len(explicit),
            "total_inferred": len(inferred)
        }
    
    def _infer_limitations(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """Infer potential limitations from methodology and experiments."""
        prompt = f"""Analyze this research paper excerpt and identify potential limitations that are not explicitly stated but can be inferred from the methodology, experimental setup, dataset, or results.

        Paper excerpt:
        {text[:3000]}

        Look for:
        1. Dataset limitations (size, diversity, representativeness)
        2. Methodological limitations (simplifications, assumptions)
        3. Evaluation limitations (benchmarks, metrics)
        4. Generalization limitations
        5. Scalability concerns
        6. Reproducibility issues

        For each limitation, provide:
        - The limitation description
        - Your reasoning (what evidence supports this inference)
        - Confidence level (low/medium/high)

        Format each limitation as:
        LIMITATION: [description]
        REASONING: [your reasoning]
        CONFIDENCE: [low/medium/high]
        """
        
        try:
            response = self.llm.generate(prompt, temperature=0.1)
            return self._parse_limitation_response(response)
        except Exception as e:
            print(f"Error inferring limitations: {e}")
            return []
    
    def _parse_limitation_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured limitations."""
        limitations = []
        lines = response.strip().split('\n')
        
        current_limitation = {}
        for line in lines:
            if line.startswith('LIMITATION:'):
                if current_limitation:
                    limitations.append(current_limitation)
                current_limitation = {
                    'text': line.replace('LIMITATION:', '').strip(),
                    'type': 'inferred'
                }
            elif line.startswith('REASONING:'):
                if current_limitation:
                    current_limitation['reasoning'] = line.replace('REASONING:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                if current_limitation:
                    confidence = line.replace('CONFIDENCE:', '').strip().lower()
                    current_limitation['confidence'] = confidence
        
        if current_limitation and 'text' in current_limitation:
            limitations.append(current_limitation)
        
        return limitations