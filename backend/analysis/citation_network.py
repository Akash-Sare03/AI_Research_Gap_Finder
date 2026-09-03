# backend/analysis/citation_network.py

import re
from typing import Dict, Any, List
from collections import defaultdict

class CitationNetwork:
    """Extract and visualize citation networks."""
    
    def extract_citations(self, text: str, external_sources: List = None) -> Dict[str, Any]:
        """Extract citations from the paper."""
        
        citations = {
            "internal": [],
            "external": [],
            "by_category": defaultdict(list),
            "total": 0
        }
        
        # Extract numbered citations like [1], [2], [63]
        internal_pattern = r'\[(\d+)\]'
        internal_matches = re.findall(internal_pattern, text)
        for match in internal_matches:
            citations["internal"].append(match)
        
        # Extract author-year citations like (Author, 2024)
        author_pattern = r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(\d{4})\)'
        author_matches = re.findall(author_pattern, text)
        for author, year in author_matches:
            citations["external"].append({
                "author": author,
                "year": year,
                "type": "author_year"
            })
        
        # Extract external sources if provided
        if external_sources:
            for source in external_sources:
                if isinstance(source, dict):
                    citations["external"].append({
                        "title": source.get("title", ""),
                        "url": source.get("url", ""),
                        "type": "web_source"
                    })
        
        # Categorize citations
        for cite in citations["internal"][:10]:
            # Try to categorize based on context
            citations["by_category"]["General"].append(cite)
        
        citations["total"] = len(citations["internal"]) + len(citations["external"])
        
        return citations
    
    def format_citation_network(self, citations: Dict[str, Any]) -> str:
        """Format citation network for display."""
        
        output = []
        output.append("## 📚 Citation Network\n")
        
        if citations["internal"]:
            output.append(f"**Internal Citations:** {len(citations['internal'])}")
            output.append(f"  {', '.join(citations['internal'][:10])}")
            if len(citations["internal"]) > 10:
                output.append(f"  ... and {len(citations['internal']) - 10} more")
            output.append("")
        
        if citations["external"]:
            output.append(f"**External Citations:** {len(citations['external'])}")
            for cite in citations["external"][:5]:
                if isinstance(cite, dict):
                    if cite.get("author"):
                        output.append(f"  - {cite['author']} ({cite['year']})")
                    elif cite.get("title"):
                        output.append(f"  - {cite['title']}")
            output.append("")
        
        # Categorized
        if citations["by_category"]:
            output.append("**Citations by Category:**")
            for category, items in citations["by_category"].items():
                if items:
                    output.append(f"  - {category}: {len(items)}")
        
        return "\n".join(output)