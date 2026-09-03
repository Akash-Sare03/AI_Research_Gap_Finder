# frontend/components/visualization.py

import streamlit as st
import pandas as pd
import re
from collections import Counter

def create_visualization_dashboard(analysis: dict):
    """Create a visualization dashboard for the analysis."""
    
    if not analysis:
        st.warning("No analysis data available for visualization.")
        return
    
    st.subheader("📊 Analysis Dashboard")
    
    # ============================================
    # SAFELY extract metrics with fallbacks
    # ============================================
    
    # Count findings by category - with safe fallbacks
    categories = {
        "Explicit Limitations": len(analysis.get("explicit_limitations", [])),
        "Inferred Limitations": len(analysis.get("inferred_limitations", [])),
        "Research Gaps": len(analysis.get("research_gaps", [])),
        "Novel Insights": len(analysis.get("novel_discoveries", [])),
        "Improvements": len(analysis.get("suggested_improvements", []))
    }
    
    # Also check if data is in sections format
    sections = analysis.get("sections", {})
    if sections:
        # Override with section counts if available
        for key in sections.keys():
            key_upper = key.upper()
            if "EXPLICIT" in key_upper and "LIMITATION" in key_upper:
                categories["Explicit Limitations"] = len(sections[key].split('\n')) if sections[key] else 0
            elif "INFERRED" in key_upper and "LIMITATION" in key_upper:
                categories["Inferred Limitations"] = len(sections[key].split('\n')) if sections[key] else 0
            elif "RESEARCH GAPS" in key_upper:
                categories["Research Gaps"] = len(sections[key].split('\n')) if sections[key] else 0
            elif "NOVEL" in key_upper and "INSIGHT" in key_upper:
                categories["Novel Insights"] = len(sections[key].split('\n')) if sections[key] else 0
            elif "SUGGESTED IMPROVEMENTS" in key_upper:
                categories["Improvements"] = len(sections[key].split('\n')) if sections[key] else 0
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Explicit", categories["Explicit Limitations"])
    with col2:
        st.metric("🧠 Inferred", categories["Inferred Limitations"])
    with col3:
        st.metric("🔬 Gaps", categories["Research Gaps"])
    with col4:
        st.metric("💡 Insights", categories["Novel Insights"])
    with col5:
        st.metric("🚀 Improvements", categories["Improvements"])
    
    # ============================================
    # Priority Distribution
    # ============================================
    
    st.subheader("📊 Priority Distribution")
    
    # Extract gaps from different possible locations
    gaps_text = ""
    
    # Try from sections first
    for key in sections.keys():
        if "RESEARCH GAPS" in key.upper():
            gaps_text = sections[key]
            break
    
    # If not found, try from research_gaps list
    if not gaps_text:
        gaps = analysis.get("research_gaps", [])
        if gaps:
            gaps_text = "\n".join([g.get("description", "") for g in gaps])
    
    # Count priorities
    gap_priorities = {"High": 0, "Medium": 0, "Low": 0}
    
    if gaps_text:
        # Check for priority indicators
        high_count = gaps_text.upper().count("HIGH PRIORITY")
        medium_count = gaps_text.upper().count("MEDIUM PRIORITY")
        low_count = gaps_text.upper().count("LOW PRIORITY")
        
        if high_count > 0:
            gap_priorities["High"] = high_count
        if medium_count > 0:
            gap_priorities["Medium"] = medium_count
        if low_count > 0:
            gap_priorities["Low"] = low_count
        
        # Also check for numbered gaps
        gap_items = re.findall(r'\d+\.\s*\*?\*?([^*\n]+)', gaps_text)
        for item in gap_items:
            item_lower = item.lower()
            if "high" in item_lower or "critical" in item_lower:
                gap_priorities["High"] += 1
            elif "medium" in item_lower:
                gap_priorities["Medium"] += 1
            elif "low" in item_lower:
                gap_priorities["Low"] += 1
    
    # If still all zeros, try to count from sections
    if sum(gap_priorities.values()) == 0 and sections:
        for key in sections.keys():
            if "RESEARCH GAPS" in key.upper():
                content = sections[key]
                # Count lines that look like gaps
                lines = content.split('\n')
                gap_count = sum(1 for line in lines if re.match(r'^\d+\.', line.strip()))
                if gap_count > 0:
                    # Distribute evenly if no priority info
                    gap_priorities["High"] = max(1, gap_count // 3)
                    gap_priorities["Medium"] = max(1, gap_count // 3)
                    gap_priorities["Low"] = max(0, gap_count - gap_priorities["High"] - gap_priorities["Medium"])
    
    # If still no gaps, show a message
    if sum(gap_priorities.values()) == 0:
        st.info("No priority data available. Upload a paper and analyze it first.")
    else:
        # Display as horizontal bars
        total = sum(gap_priorities.values()) or 1
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"🔴 **High Priority: {gap_priorities['High']}**")
            st.progress(gap_priorities["High"] / total)
        with cols[1]:
            st.markdown(f"🟡 **Medium Priority: {gap_priorities['Medium']}**")
            st.progress(gap_priorities["Medium"] / total)
        with cols[2]:
            st.markdown(f"🟢 **Low Priority: {gap_priorities['Low']}**")
            st.progress(gap_priorities["Low"] / total)
    
    # ============================================
    # Performance Metrics
    # ============================================
    
    metrics = extract_metrics(analysis)
    if metrics:
        st.subheader("📈 Performance Metrics")
        
        # Create a simple table
        df = pd.DataFrame(list(metrics.items()), columns=["Metric", "Value"])
        st.dataframe(df, use_container_width=True)
    
    # ============================================
    # External Sources
    # ============================================
    
    external = analysis.get("external_sources", [])
    if external:
        st.subheader("🌐 External Sources")
        st.metric("Total External Sources", len(external))
        with st.expander("View External Sources"):
            for source in external[:5]:
                if isinstance(source, dict):
                    title = source.get('title', source.get('source', 'Unknown'))
                    url = source.get('url', '')
                    if url:
                        st.write(f"- [{title}]({url})")
                    else:
                        st.write(f"- {title}")
                else:
                    st.write(f"- {source}")
    
    # ============================================
    # Quick Stats from Sections
    # ============================================
    
    if sections:
        st.subheader("📄 Section Summary")
        section_names = list(sections.keys())
        st.write(f"**Total Sections:** {len(section_names)}")
        st.write(f"**Sections:** {', '.join(section_names[:5])}" + ("..." if len(section_names) > 5 else ""))


def extract_metrics(analysis: dict) -> dict:
    """Extract performance metrics from analysis."""
    metrics = {}
    
    # Get full analysis text
    full_text = analysis.get("full_analysis", "")
    
    if not full_text:
        # Try to get from sections
        sections = analysis.get("sections", {})
        for key in sections.keys():
            if sections[key]:
                full_text += sections[key] + "\n"
    
    if not full_text:
        return metrics
    
    # Extract numbers with percentages
    matches = re.findall(r'(\d+\.?\d*)\s*%', full_text)
    if matches:
        for i, m in enumerate(matches[:5]):
            try:
                val = float(m)
                if 0 < val < 100:
                    metrics[f"Metric {i+1}"] = f"{val}%"
            except:
                pass
    
    # Check for specific benchmark names
    benchmarks = ["GPQA", "MMLU", "HumanEval", "MBPP", "HLE", "CritPt", "BrowseComp", "DeepSWE"]
    for bench in benchmarks:
        if bench in full_text:
            # Try to find the value
            pattern = rf'{bench}.*?(\d+\.?\d*)\s*%'
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                try:
                    metrics[bench] = f"{float(match.group(1))}%"
                except:
                    metrics[bench] = "Mentioned"
            else:
                metrics[bench] = "Mentioned"
    
    return metrics