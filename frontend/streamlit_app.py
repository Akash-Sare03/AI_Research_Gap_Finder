# frontend/streamlit_app.py

import streamlit as st
import os
import sys
import time
from pathlib import Path
import re
import json
from datetime import datetime
import importlib

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="AI Research Gap Finder",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.service = None
    st.session_state.current_analysis = None
    st.session_state.chat_history = []
    st.session_state.app_ready = False
    st.session_state.current_paper_id = None
    st.session_state.pending_question = None
    st.session_state.show_dashboard = False
    st.session_state.export_report = False
    st.session_state.compare_online = False
    st.session_state.modules_loaded = {
        "visualization": False,
        "report": False,
        "comparator": False,
        "metrics": False,
        "citation": False
    }

# ============================================
# LAZY LOADING FUNCTIONS
# ============================================

def lazy_load_visualization():
    """Lazy load visualization module only when needed."""
    if not st.session_state.modules_loaded["visualization"]:
        try:
            # Import only when needed
            from frontend.components.visualization import create_visualization_dashboard
            st.session_state._vis_module = create_visualization_dashboard
            st.session_state.modules_loaded["visualization"] = True
            return st.session_state._vis_module
        except ImportError as e:
            st.warning(f"Visualization module not available: {e}")
            return None
    return st.session_state._vis_module if hasattr(st.session_state, '_vis_module') else None


def lazy_load_report_generator():
    """Lazy load report generator only when needed."""
    if not st.session_state.modules_loaded["report"]:
        try:
            from backend.services.report_generator import ReportGenerator
            st.session_state._report_module = ReportGenerator()
            st.session_state.modules_loaded["report"] = True
            return st.session_state._report_module
        except ImportError as e:
            st.warning(f"Report generator not available: {e}")
            return None
    return st.session_state._report_module if hasattr(st.session_state, '_report_module') else None


def lazy_load_comparator():
    """Lazy load online comparator only when needed."""
    if not st.session_state.modules_loaded["comparator"]:
        try:
            from backend.analysis.online_comparator import OnlineComparator
            st.session_state._comparator_module = OnlineComparator()
            st.session_state.modules_loaded["comparator"] = True
            return st.session_state._comparator_module
        except ImportError as e:
            st.warning(f"Online comparator not available: {e}")
            return None
    return st.session_state._comparator_module if hasattr(st.session_state, '_comparator_module') else None


def lazy_load_metrics_extractor():
    """Lazy load metrics extractor only when needed."""
    if not st.session_state.modules_loaded["metrics"]:
        try:
            from backend.analysis.metrics_extractor import MetricsExtractor
            st.session_state._metrics_module = MetricsExtractor()
            st.session_state.modules_loaded["metrics"] = True
            return st.session_state._metrics_module
        except ImportError as e:
            st.warning(f"Metrics extractor not available: {e}")
            return None
    return st.session_state._metrics_module if hasattr(st.session_state, '_metrics_module') else None


def lazy_load_citation_network():
    """Lazy load citation network only when needed."""
    if not st.session_state.modules_loaded["citation"]:
        try:
            from backend.analysis.citation_network import CitationNetwork
            st.session_state._citation_module = CitationNetwork()
            st.session_state.modules_loaded["citation"] = True
            return st.session_state._citation_module
        except ImportError as e:
            st.warning(f"Citation network not available: {e}")
            return None
    return st.session_state._citation_module if hasattr(st.session_state, '_citation_module') else None


# ============================================
# LAZY SERVICE INITIALIZATION
# ============================================
def init_service():
    """Lazy initialize the service only when needed."""
    if st.session_state.service is None:
        try:
            status = st.empty()
            status.info("⏳ Loading Research Service...")
            
            # Import only when needed
            from backend.core.config import Config
            status.info("✅ Config loaded")
            
            from backend.services.research_service import ResearchService
            status.info("⏳ Initializing Research Service...")
            
            st.session_state.service = ResearchService()
            st.session_state.initialized = True
            st.session_state.app_ready = True
            status.empty()
            return True
            
        except Exception as e:
            st.error(f"❌ Service initialization failed: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.initialized = False
            return False
    return True


# ============================================
# FORMATTING FUNCTIONS
# ============================================

def display_gaps_with_priority(gaps_text: str) -> str:
    """Display research gaps with priority badges."""
    if not gaps_text or gaps_text.strip() == "":
        return "No research gaps identified."
    
    lines = gaps_text.split('\n')
    formatted = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if 'HIGH PRIORITY' in line.upper():
            formatted.append("\n### 🔴 HIGH PRIORITY GAPS\n")
        elif 'MEDIUM PRIORITY' in line.upper():
            formatted.append("\n### 🟡 MEDIUM PRIORITY GAPS\n")
        elif 'LOW PRIORITY' in line.upper():
            formatted.append("\n### 🟢 LOW PRIORITY GAPS\n")
        elif re.match(r'^(\d+\.\s*|-\s*|\*\s*)', line):
            clean = re.sub(r'^[\d\.\*\-•\s]+', '', line)
            if clean and len(clean) > 5:
                if ':' in clean and len(clean) < 100:
                    formatted.append(f"**{clean}**")
                else:
                    formatted.append(f"• {clean}")
        elif line.startswith('- Evidence:') or line.startswith('- Impact:'):
            formatted.append(f"  *{line}*")
        elif len(line) > 5 and not line.startswith('###'):
            formatted.append(line)
    
    return '\n'.join(formatted)


def get_suggested_questions(analysis: dict) -> list:
    """Generate suggested questions based on paper content."""
    
    suggestions = []
    sections = analysis.get("sections", {})
    
    # Section-based questions
    section_questions = {
        "EXECUTIVE SUMMARY": ["What is this paper about?", "What are the main contributions?"],
        "EXPLICIT LIMITATIONS": ["What are the explicit limitations?"],
        "INFERRED LIMITATIONS": ["What limitations can be inferred?"],
        "RESEARCH GAPS": ["What are the research gaps?", "What needs further research?"],
        "SUGGESTED IMPROVEMENTS": ["What improvements are suggested?", "How could this research be enhanced?"],
        "ETHICAL CONCERNS": ["What are the ethical concerns?"],
        "COMPARISON WITH EXISTING WORK": ["How does this compare to other research?", "What are the direct competitors?"],
        "NOVEL INSIGHTS": ["What novel insights can you find?"]
    }
    
    for section, questions in section_questions.items():
        for key in sections.keys():
            if section in key.upper() and sections[key]:
                suggestions.extend(questions)
                break
    
    # General questions
    general_questions = [
        "What methodology was used?",
        "What are the key results?",
        "What datasets were used?",
        "What are the main conclusions?",
        "What is the significance of this research?"
    ]
    
    for q in general_questions:
        if q not in suggestions:
            suggestions.append(q)
    
    return suggestions[:10]


def format_complete_analysis_with_sections(sections: dict) -> str:
    """Format complete analysis with all sections."""
    if not sections:
        return "No analysis available."
    
    output = []
    
    section_order = [
        ("EXECUTIVE SUMMARY", "📊"),
        ("EXPLICIT LIMITATIONS", "📋"),
        ("INFERRED LIMITATIONS", "🧠"),
        ("RESEARCH GAPS", "🔬"),
        ("NOVEL INSIGHTS", "💡"),
        ("SUGGESTED IMPROVEMENTS", "🚀"),
        ("ETHICAL CONCERNS", "⚖️"),
        ("COMPARISON WITH EXISTING WORK", "📚"),
        ("SOURCES REFERENCES", "📄")
    ]
    
    for section_name, emoji in section_order:
        content = None
        for key in sections.keys():
            if section_name.upper() in key.upper():
                content = sections[key]
                break
        
        if content and content.strip():
            output.append(f"## {emoji} {section_name}\n")
            if "RESEARCH GAPS" in section_name.upper():
                output.append(display_gaps_with_priority(content))
            else:
                output.append(content)
            output.append("")
    
    return "\n".join(output)


def generate_research_response(query: str, analysis: dict, service) -> str:
    """Generate a response using RAG with confidence scoring."""
    
    paper_id = analysis.get("paper_id", "")
    
    if not paper_id:
        return "⚠️ Paper ID not found. Please re-analyze the paper."
    
    # Use RAG to answer
    rag_result = service.answer_question(query, paper_id)
    
    if rag_result.get("success"):
        answer = rag_result.get("answer", "")
        sources = rag_result.get("sources", [])
        confidence = rag_result.get("confidence_msg", "")
        confidence_emoji = rag_result.get("confidence_emoji", "🟡")
        confidence_score = rag_result.get("confidence_score", 0)
        
        response_parts = []
        response_parts.append(answer)
        
        # Add confidence
        response_parts.append(f"\n\n{confidence_emoji} **Confidence:** {confidence} ({confidence_score}%)")
        
        # Add sources
        if sources:
            for source in sources[:3]:
                response_parts.append(f"- Paper: {source.get('paper_id', 'unknown')} (Page {source.get('page', '?')})")
        
        # External used
        if rag_result.get("external_used"):
            response_parts.append("\n\n🌐 *Some information was sourced from external research.*")
        
        # Context info
        chunks = rag_result.get("context_chunks", 0)
        if chunks > 0:
            response_parts.append(f"\n📄 *Found {chunks} relevant passages from the paper.*")
        
        return "\n".join(response_parts)
    
    else:
        # Fallback to sections
        sections = analysis.get("sections", {})
        return format_complete_analysis_with_sections(sections)


# ============================================
# TITLE
# ============================================
st.title("🔬 AI Research Gap Finder")
st.markdown("Upload research papers and discover research gaps with full transparency")

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("📚 Research Library")
    
    if not st.session_state.initialized:
        st.info("Click 'Start' to load the research engine")
        if st.button("🚀 Start Application", type="primary", use_container_width=True):
            with st.spinner("Loading AI models..."):
                if init_service():
                    st.success("✅ Ready!")
                    st.rerun()
                else:
                    st.error("❌ Failed to initialize")
        st.stop()
    
    st.success("✅ Application Ready")
    
    # Upload section
    st.subheader("📤 Upload Paper")
    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])
    
    compare = st.checkbox("🔍 Compare with similar papers online", value=False)
    include_external = st.checkbox("🌐 Include external research", value=True)
    
    if uploaded_file:
        if st.button("🔬 Analyze Paper", type="primary", use_container_width=True):
            with st.spinner("Analyzing paper..."):
                try:
                    from backend.core.config import Config
                    upload_dir = Config.UPLOAD_DIR
                    Path(upload_dir).mkdir(parents=True, exist_ok=True)
                    file_path = os.path.join(upload_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    result = st.session_state.service.upload_and_analyze_paper(
                        file_path, compare=compare, include_external=include_external
                    )
                    
                    if result["status"] == "success":
                        st.success(f"✅ Paper analyzed: {result['paper_id']}")
                        st.session_state.current_analysis = result["analysis"]
                        st.session_state.current_paper_id = result["paper_id"]
                        st.session_state.chat_history = []
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": f"✅ Paper **{result['paper_id']}** analyzed successfully!\n\nAsk me anything about this paper."
                        })
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.subheader("📄 Your Papers")
    
    try:
        papers = st.session_state.service.get_all_papers()
        if papers:
            for paper in papers:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"📄 {paper['paper_id']}", key=f"view_{paper['paper_id']}"):
                        with st.spinner("Loading analysis..."):
                            analysis = st.session_state.service.get_paper_analysis(paper["paper_id"])
                            st.session_state.current_analysis = analysis.get("analysis", {})
                            st.session_state.current_paper_id = paper["paper_id"]
                            st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{paper['paper_id']}"):
                        st.session_state.service.delete_paper(paper["paper_id"])
                        st.rerun()
        else:
            st.info("No papers uploaded yet")
    except Exception as e:
        st.error(f"Error loading papers: {str(e)}")
    
    st.divider()
    try:
        stats = st.session_state.service.get_stats()
        col1, col2 = st.columns(2)
        col1.metric("Total Papers", stats["total_papers"])
        col2.metric("Total Chunks", stats["total_chunks"])
    except Exception as e:
        pass

# ============================================
# MAIN CHAT INTERFACE
# ============================================

if not st.session_state.app_ready:
    st.info("👈 Click 'Start Application' in the sidebar to begin")
    st.stop()

st.header("💬 Research Analyst")

# ============================================
# FEATURE: Suggested Questions (Lazy Load)
# ============================================
if st.session_state.current_analysis:
    with st.expander("💡 Suggested Questions", expanded=False):
        suggestions = get_suggested_questions(st.session_state.current_analysis)
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            col = cols[i % 2]
            if col.button(f"🔍 {suggestion}", key=f"suggest_{i}"):
                st.session_state.pending_question = suggestion
                st.rerun()

# ============================================
# FEATURE: Quick Actions
# ============================================
if st.session_state.current_analysis:
    with st.expander("⚡ Quick Actions", expanded=False):
        action_cols = st.columns(3)
        
        with action_cols[0]:
            if st.button("📊 Show Dashboard", use_container_width=True):
                st.session_state.show_dashboard = True
                st.rerun()
        
        with action_cols[1]:
            if st.button("📥 Export Report", use_container_width=True):
                st.session_state.export_report = True
                st.rerun()
        
        with action_cols[2]:
            if st.button("🌐 Compare Online", use_container_width=True):
                st.session_state.compare_online = True
                st.rerun()
        
        with action_cols[0]:
            if st.button("💡 Discover Novel Insights", use_container_width=True):
                st.session_state.show_novel_discovery = True
                st.rerun()

# ============================================
# FEATURE: Visualization Dashboard (Lazy Loaded)
# ============================================
if hasattr(st.session_state, 'show_dashboard') and st.session_state.show_dashboard:
    st.divider()
    #st.subheader("📊 Analysis Dashboard")
    
    try:
        vis_module = lazy_load_visualization()
        if vis_module:
            # Check if analysis has data
            if st.session_state.current_analysis:
                vis_module(st.session_state.current_analysis)
            else:
                st.warning("No analysis data available. Please analyze a paper first.")
        else:
            st.info("Visualization module not available. Install required dependencies.")
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    if st.button("Close Dashboard"):
        st.session_state.show_dashboard = False
        st.rerun()
    st.divider()


# ============================================
# FEATURE: Novel Discovery (Lazy Loaded)
# ============================================
if hasattr(st.session_state, 'show_novel_discovery') and st.session_state.show_novel_discovery:
    st.divider()
    st.subheader("💡 Novel Discovery Engine")
    st.info("This engine uses mathematical reasoning, pattern detection, and logical inference to discover NEW insights not mentioned in the paper.")
    
    with st.spinner("🔍 Discovering novel insights..."):
        try:
            from backend.analysis.novel_discovery import NovelDiscovery
            discoverer = NovelDiscovery()
            
            full_text = st.session_state.current_analysis.get("full_analysis", "")
            sections = st.session_state.current_analysis.get("sections", {})
            metadata = st.session_state.current_analysis.get("paper_metadata", {})
            
            discoveries = discoverer.discover(full_text, sections)
            formatted = discoverer.format_for_display(discoveries)
            st.markdown(formatted)
            
        except Exception as e:
            st.error(f"Error discovering novel insights: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    if st.button("Close Novel Discovery"):
        st.session_state.show_novel_discovery = False
        st.rerun()
    st.divider()

# ============================================
# FEATURE: Export Report (Lazy Loaded)
# ============================================
if hasattr(st.session_state, 'export_report') and st.session_state.export_report:
    report_gen = lazy_load_report_generator()
    if report_gen:
        report = report_gen.generate_markdown_report(
            st.session_state.current_analysis,
            st.session_state.current_paper_id
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Report (Markdown)",
                data=report,
                file_name=f"research_analysis_{st.session_state.current_paper_id}.md",
                mime="text/markdown"
            )
        
        with col2:
            json_report = report_gen.export_to_json(st.session_state.current_analysis)
            st.download_button(
                label="📥 Download Report (JSON)",
                data=json.dumps(json_report, indent=2),
                file_name=f"research_analysis_{st.session_state.current_paper_id}.json",
                mime="application/json"
            )
    else:
        st.warning("Report generator not available.")
    
    if st.button("Close Export"):
        st.session_state.export_report = False
        st.rerun()
    st.divider()

# ============================================
# FEATURE: Online Comparison (Lazy Loaded)
# ============================================
if hasattr(st.session_state, 'compare_online') and st.session_state.compare_online:
    comparator = lazy_load_comparator()
    if comparator:
        with st.spinner("🔍 Searching online for similar research..."):
            paper_title = st.session_state.current_analysis.get("paper_metadata", {}).get("title", "")
            paper_text = st.session_state.current_analysis.get("full_analysis", "")[:2000]
            
            if paper_title:
                result = comparator.find_similar_research(paper_title, paper_text)
                
                st.subheader("🌐 Online Research Comparison")
                
                if result.get("similar_papers"):
                    st.write(f"Found **{result['total_found']}** similar papers online")
                    st.write(f"**Keywords:** {result.get('keywords', 'N/A')}")
                    
                    with st.expander("📚 Similar Papers Found", expanded=True):
                        for i, paper in enumerate(result["similar_papers"][:5], 1):
                            st.markdown(f"**{i}. {paper.get('title', 'Unknown')}**")
                            st.write(f"   - {paper.get('snippet', 'No snippet')[:200]}...")
                            if paper.get('url'):
                                st.write(f"   - 🔗 [Link]({paper['url']})")
                            st.divider()
                    
                    if result.get("comparison_analysis"):
                        st.subheader("📊 Comparison Analysis")
                        st.markdown(result["comparison_analysis"])
                else:
                    st.info("No similar research found online.")
            else:
                st.warning("Paper title not available for comparison.")
    else:
        st.warning("Online comparator not available.")
    
    if st.button("Close Comparison"):
        st.session_state.compare_online = False
        st.rerun()
    st.divider()

# ============================================
# FEATURE: Performance Metrics (Lazy Loaded)
# ============================================
if st.session_state.current_analysis:
    metrics_extractor = lazy_load_metrics_extractor()
    if metrics_extractor:
        full_text = st.session_state.current_analysis.get("full_analysis", "")
        metrics = metrics_extractor.extract_metrics(full_text)
        
        if metrics.get("percentages") or metrics.get("models") or metrics.get("benchmarks"):
            with st.expander("📊 Performance Metrics Extracted", expanded=False):
                if metrics.get("percentages"):
                    st.write(f"**Performance Scores:** {len(metrics['percentages'])} found")
                    if metrics.get("stats"):
                        stats = metrics["stats"]
                        st.write(f"- Range: {stats['min']:.1f}% to {stats['max']:.1f}%")
                        st.write(f"- Average: {stats['average']:.1f}%")
                
                if metrics.get("models"):
                    st.write(f"**Models Mentioned:** {', '.join(metrics['models'][:5])}")
                
                if metrics.get("benchmarks"):
                    st.write(f"**Benchmarks:** {', '.join(metrics['benchmarks'][:8])}")

# ============================================
# FEATURE: Citation Network (Lazy Loaded)
# ============================================
if st.session_state.current_analysis:
    citation_module = lazy_load_citation_network()
    if citation_module:
        full_text = st.session_state.current_analysis.get("full_analysis", "")
        external_sources = st.session_state.current_analysis.get("external_sources", [])
        
        citations = citation_module.extract_citations(full_text, external_sources)
        
        if citations.get("total", 0) > 0:
            with st.expander("📚 Citation Network", expanded=False):
                st.write(f"**Total Citations Found:** {citations['total']}")
                
                if citations.get("internal"):
                    st.write(f"**Internal Citations:** {len(citations['internal'])}")
                    st.write(f"  {', '.join(citations['internal'][:15])}")
                
                if citations.get("external"):
                    st.write(f"**External Citations:** {len(citations['external'])}")
                    for cite in citations["external"][:5]:
                        if isinstance(cite, dict):
                            if cite.get("author"):
                                st.write(f"  - {cite['author']} ({cite['year']})")
                            elif cite.get("title"):
                                st.write(f"  - {cite['title']}")

# ============================================
# CHAT HISTORY & INPUT
# ============================================

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.current_analysis:
    st.info("📄 Upload and analyze a paper first from the sidebar")
    st.stop()

# Show current paper info
paper_id = st.session_state.current_analysis.get("paper_id", "Unknown")
st.caption(f"📄 Currently analyzing: **{paper_id}**")

# Chat input
prompt = None

# Check for pending question from suggestions
if hasattr(st.session_state, 'pending_question') and st.session_state.pending_question:
    prompt = st.session_state.pending_question
    st.session_state.pending_question = None
else:
    prompt = st.chat_input("Ask anything about your research paper...")

if prompt:
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching the paper for relevant information..."):
            try:
                response = generate_research_response(
                    prompt, 
                    st.session_state.current_analysis,
                    st.session_state.service
                )
                
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🔬 AI Research Gap Finder - Powered by Lazy Loading RAG + External Research + Confidence Scoring")