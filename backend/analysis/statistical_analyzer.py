from typing import List, Dict, Any, Optional, Tuple
import re
import math
from ..models.evidence import Finding, Evidence, Source, EvidenceType

class StatisticalAnalyzer:
    """
    Performs statistical analysis with full transparency.
    Every calculation shows the formula, values used, and source.
    """
    
    def __init__(self, reasoning_engine):
        self.reasoning_engine = reasoning_engine
    
    def analyze_performance(self, chunks: List[Dict[str, Any]], paper_id: str) -> List[Finding]:
        """Analyze performance metrics with transparent calculations."""
        findings = []
        
        # Extract all numbers from chunks
        all_numbers = []
        number_sources = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            page = chunk.get("metadata", {}).get("page_number", 1)
            chunk_id = chunk.get("chunk_id", "")
            
            # Find numbers with percentages
            matches = re.findall(r'(\d+\.?\d*)\s*%', text)
            for match in matches:
                try:
                    value = float(match)
                    all_numbers.append(value)
                    number_sources.append({
                        "value": value,
                        "page": page,
                        "chunk_id": chunk_id,
                        "text": self._get_context(text, match)
                    })
                except:
                    pass
        
        if len(all_numbers) >= 3:
            # Calculate statistics
            sorted_nums = sorted(all_numbers)
            mean = sum(all_numbers) / len(all_numbers)
            variance = sum((x - mean) ** 2 for x in all_numbers) / len(all_numbers)
            std_dev = math.sqrt(variance)
            max_val = max(all_numbers)
            min_val = min(all_numbers)
            range_val = max_val - min_val
            
            # Create finding for variation
            if std_dev > 5:  # Significant variation
                calculation = f"""
                Mean = {mean:.2f}%
                Standard Deviation = {std_dev:.2f}%
                Range = {range_val:.2f}% (Min: {min_val:.2f}%, Max: {max_val:.2f}%)
                Variance = {variance:.2f}
                """
                
                reasoning = f"""
                The standard deviation of {std_dev:.2f}% indicates significant variation in reported performance metrics.
                This could mean:
                1. Different evaluation protocols were used
                2. The methods have genuine performance differences
                3. Some results are outliers
                """
                
                finding = self.reasoning_engine.create_calculated_finding(
                    description=f"Performance varies significantly (±{std_dev:.2f}%)",
                    paper_id=paper_id,
                    calculation=calculation,
                    reasoning=reasoning,
                    metric_values={
                        "mean": mean,
                        "std_dev": std_dev,
                        "min": min_val,
                        "max": max_val
                    },
                    page=number_sources[0]["page"] if number_sources else 1,
                    chunk_id=number_sources[0]["chunk_id"] if number_sources else "",
                    category="statistical_insight"
                )
                findings.append(finding)
            
            # Find potential outliers
            outlier_threshold = mean + 2 * std_dev
            for source in number_sources:
                if abs(source["value"] - mean) > outlier_threshold:
                    calculation = f"""
                    Value: {source['value']}%
                    Mean: {mean:.2f}%
                    Std Dev: {std_dev:.2f}%
                    Difference from Mean: {abs(source['value'] - mean):.2f}%
                    Threshold: {outlier_threshold:.2f}%
                    """
                    
                    reasoning = f"""
                    The value {source['value']}% deviates from the mean by {abs(source['value'] - mean):.2f}%,
                    which is more than 2 standard deviations ({std_dev:.2f}%).
                    This could indicate:
                    1. A different evaluation protocol
                    2. A genuine performance difference
                    3. A reporting error
                    """
                    
                    finding = self.reasoning_engine.create_calculated_finding(
                        description=f"Potential outlier: {source['value']}% (vs mean {mean:.2f}%)",
                        paper_id=paper_id,
                        calculation=calculation,
                        reasoning=reasoning,
                        metric_values={"value": source["value"], "mean": mean},
                        page=source["page"],
                        chunk_id=source["chunk_id"],
                        category="statistical_insight"
                    )
                    findings.append(finding)
        
        return findings
    
    def _get_context(self, text: str, match: str) -> str:
        """Get context around a matched value."""
        import re
        for sentence in re.split(r'[.!?]+', text):
            if match in sentence:
                return sentence.strip()
        return text[:100]