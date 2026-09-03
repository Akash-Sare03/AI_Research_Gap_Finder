# backend/analysis/metrics_extractor.py

import re
from typing import Dict, Any, List
from collections import defaultdict

class MetricsExtractor:
    """Extract and visualize performance metrics from papers."""
    
    def extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extract all performance metrics from text."""
        
        metrics = {
            "percentages": [],
            "numbers": [],
            "benchmarks": [],
            "models": []
        }
        
        # Extract percentages
        percentage_pattern = r'(\d+\.?\d*)\s*%'
        percentages = re.findall(percentage_pattern, text)
        for p in percentages:
            try:
                metrics["percentages"].append(float(p))
            except:
                pass
        
        # Extract actual model names (not generic words)
        model_patterns = [
            r'(Claude|GPT|Gemini|LLaMA|DeepSeek|Kimi|GLM|ChatGPT|Bard|Cohere|Anthropic)\s*[-\w]*',
            r'([A-Z][a-z]+[-_ ]?[A-Z]?[a-z]+)\s+(?:model|architecture|system)',
            r'([A-Z]{2,}[0-9]*(?:-[A-Z0-9]+)?)'
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Filter out generic words
                if isinstance(match, str):
                    clean = match.strip()
                    if len(clean) > 2 and not clean.lower() in ['the', 'and', 'for', 'with', 'new', 'old']:
                        metrics["models"].append(clean)
        
        # Extract benchmark names
        benchmark_names = [
            "GPQA", "MMLU", "HumanEval", "MBPP", "HLE", "CritPt",
            "BrowseComp", "DeepSWE", "ProgramBench", "FrontierSWE",
            "SWE-Marathon", "Terminal-Bench", "PostTrainBench",
            "MLS-Bench", "SciCode", "DeepSearchQA", "ResearchRubrics"
        ]
        for bench in benchmark_names:
            if bench in text:
                metrics["benchmarks"].append(bench)
        
        # Deduplicate
        metrics["models"] = list(set(metrics["models"]))
        metrics["benchmarks"] = list(set(metrics["benchmarks"]))
        
        # Calculate statistics
        if metrics["percentages"]:
            metrics["stats"] = {
                "count": len(metrics["percentages"]),
                "average": sum(metrics["percentages"]) / len(metrics["percentages"]),
                "max": max(metrics["percentages"]),
                "min": min(metrics["percentages"])
            }
        
        # Remove generic entries
        generic_words = ['improving', 'existing', 'new', 'theoretical', 'the', 'for', 'with']
        metrics["models"] = [m for m in metrics["models"] if m.lower() not in generic_words]
        
        return metrics
    
    def format_for_display(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for display."""
        
        output = []
        output.append("## 📊 Performance Metrics\n")
        
        if metrics.get("percentages"):
            output.append(f"**Performance Scores Found:** {len(metrics['percentages'])}")
            output.append(f"- Range: {min(metrics['percentages']):.1f}% to {max(metrics['percentages']):.1f}%")
            output.append(f"- Average: {sum(metrics['percentages']) / len(metrics['percentages']):.1f}%\n")
        
        if metrics.get("models"):
            output.append(f"**Models Mentioned:** {', '.join(metrics['models'][:5])}")
        
        if metrics.get("benchmarks"):
            output.append(f"**Benchmarks:** {', '.join(metrics['benchmarks'][:8])}")
        
        return "\n".join(output)