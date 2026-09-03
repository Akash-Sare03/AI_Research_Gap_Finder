from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import json
import re
from ..core.llm import LLMService
from ..retrieval.hybrid import HybridRetriever
from ..analysis.gap_detector import GapDetector
from ..analysis.limitation_detector import LimitationDetector

# ✅ FIXED: Correct import for MemorySaver
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        # Fallback - create a simple memory saver
        class MemorySaver:
            def __init__(self):
                self.checkpoints = {}
            
            def save(self, config, state):
                thread_id = config.get("configurable", {}).get("thread_id", "default")
                self.checkpoints[thread_id] = state
                return {"checkpoint_id": f"checkpoint_{len(self.checkpoints)}"}
            
            def load(self, config):
                thread_id = config.get("configurable", {}).get("thread_id", "default")
                return self.checkpoints.get(thread_id, {})

# Define state
class ResearchState(TypedDict):
    query: str
    papers: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    paper_analysis: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    response: str
    iteration: int
    needs_web_search: bool
    query_analysis: str
    critique: str
    retrieved_at_iteration: int

class ResearchAgent:
    """LangGraph-based research agent."""
    
    def __init__(self):
        self.llm = LLMService()
        self.retriever = HybridRetriever()
        self.gap_detector = GapDetector()
        self.limitation_detector = LimitationDetector()
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=self.memory)
    
    def _build_graph(self):
        """Build the research workflow graph."""
        graph = StateGraph(ResearchState)
        
        # Add nodes
        graph.add_node("understand_query", self._understand_query)
        graph.add_node("retrieve_evidence", self._retrieve_evidence)
        graph.add_node("analyze_papers", self._analyze_papers)
        graph.add_node("detect_gaps", self._detect_gaps)
        graph.add_node("critic", self._critic)
        graph.add_node("generate_response", self._generate_response)
        
        # Add edges
        graph.set_entry_point("understand_query")
        graph.add_edge("understand_query", "retrieve_evidence")
        graph.add_edge("retrieve_evidence", "analyze_papers")
        graph.add_edge("analyze_papers", "detect_gaps")
        graph.add_edge("detect_gaps", "critic")
        
        # Conditional edge from critic
        graph.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "continue": "retrieve_evidence",
                "end": "generate_response"
            }
        )
        
        graph.add_edge("generate_response", END)
        
        return graph
    
    def _understand_query(self, state: ResearchState) -> ResearchState:
        """Understand and classify the query."""
        prompt = f"""Analyze this research query and identify what information is needed:

        Query: {state['query']}

        What kind of analysis is required?
        - Paper comparison
        - Limitation identification
        - Gap detection
        - Methodological analysis
        - Dataset analysis
        - Cross-paper patterns

        Provide your analysis:
        """
        
        response = self.llm.generate(prompt, temperature=0.1)
        state["query_analysis"] = response
        state["iteration"] = state.get("iteration", 0) + 1
        
        return state
    
    def _retrieve_evidence(self, state: ResearchState) -> ResearchState:
        """Retrieve evidence from papers."""
        queries = self._generate_search_queries(state["query"])
        
        all_chunks = []
        seen_ids = set()
        
        for query in queries:
            chunks = self.retriever.retrieve(query, top_k=5)
            for chunk in chunks:
                if chunk["id"] not in seen_ids:
                    seen_ids.add(chunk["id"])
                    all_chunks.append(chunk)
        
        # Balance across papers
        if all_chunks:
            paper_groups = {}
            for chunk in all_chunks:
                paper_id = chunk["metadata"].get("paper_id", "unknown")
                if paper_id not in paper_groups:
                    paper_groups[paper_id] = []
                paper_groups[paper_id].append(chunk)
            
            balanced_chunks = []
            for paper_id, chunks in paper_groups.items():
                balanced_chunks.extend(chunks[:3])
            
            state["retrieved_chunks"] = balanced_chunks
        else:
            state["retrieved_chunks"] = []
        
        state["retrieved_at_iteration"] = state["iteration"]
        
        return state
    
    def _generate_search_queries(self, query: str) -> List[str]:
        """Generate multiple search queries for better coverage."""
        prompt = f"""Generate 3-5 search queries to find evidence for this research question:

        Query: {query}

        Focus on retrieving information about:
        - Methodology and experimental setup
        - Datasets used
        - Limitations mentioned
        - Future work directions
        - Results and findings

        Format: Return ONLY the queries, one per line.
        """
        
        response = self.llm.generate(prompt, temperature=0.3)
        queries = [query]
        
        lines = response.strip().split('\n')
        for line in lines[:3]:
            if line.strip() and len(line.strip()) > 5:
                queries.append(line.strip())
        
        return queries
    
    def _analyze_papers(self, state: ResearchState) -> ResearchState:
        """Analyze retrieved chunks from papers."""
        if not state["retrieved_chunks"]:
            state["paper_analysis"] = []
            return state
        
        chunks_by_paper = {}
        for chunk in state["retrieved_chunks"]:
            paper_id = chunk["metadata"].get("paper_id", "unknown")
            if paper_id not in chunks_by_paper:
                chunks_by_paper[paper_id] = []
            chunks_by_paper[paper_id].append(chunk)
        
        analyses = []
        for paper_id, chunks in chunks_by_paper.items():
            paper_text = "\n".join([c["text"] for c in chunks])
            
            analysis = self.limitation_detector.analyze_paper(paper_text, paper_id)
            
            methodology = self._extract_methodology(paper_text)
            dataset = self._extract_dataset(paper_text)
            results = self._extract_results(paper_text)
            
            analysis.update({
                "methodology": methodology,
                "dataset": dataset,
                "results": results,
                "chunks": chunks,
                "paper_id": paper_id
            })
            
            analyses.append(analysis)
        
        state["paper_analysis"] = analyses
        
        return state
    
    def _extract_methodology(self, text: str) -> str:
        """Extract methodology information from text."""
        prompt = f"""Extract the methodology from this research paper excerpt:

        {text[:2000]}

        Provide a brief summary of the methodology.
        """
        try:
            return self.llm.generate(prompt, temperature=0.1)
        except:
            return "Methodology could not be extracted"
    
    def _extract_dataset(self, text: str) -> str:
        """Extract dataset information from text."""
        prompt = f"""Extract the dataset information from this research paper excerpt:

        {text[:2000]}

        Provide details about:
        - Dataset name(s)
        - Size
        - Source
        - Characteristics
        """
        try:
            return self.llm.generate(prompt, temperature=0.1)
        except:
            return "Dataset could not be extracted"
    
    def _extract_results(self, text: str) -> str:
        """Extract results from text."""
        prompt = f"""Extract key results from this research paper excerpt:

        {text[:2000]}

        Provide key findings and metrics.
        """
        try:
            return self.llm.generate(prompt, temperature=0.1)
        except:
            return "Results could not be extracted"
    
    def _detect_gaps(self, state: ResearchState) -> ResearchState:
        """Detect research gaps."""
        if not state["paper_analysis"]:
            state["gaps"] = []
            return state
        
        gaps = self.gap_detector.detect_gaps(state["paper_analysis"])
        state["gaps"] = gaps
        
        return state
    
    def _critic(self, state: ResearchState) -> ResearchState:
        """Critique and verify findings."""
        if not state["paper_analysis"] and not state["gaps"]:
            state["critique"] = "No evidence found. Need more retrieval."
            state["needs_web_search"] = True
            return state
        
        prompt = f"""Critique the following research analysis:

        Query: {state['query']}
        
        Paper Analyses: {json.dumps(state['paper_analysis'], default=str, indent=2)[:3000]}
        
        Identified Gaps: {json.dumps(state['gaps'], default=str, indent=2)[:2000]}
        
        Evaluate:
        1. Are there any unsupported claims?
        2. Is enough evidence provided?
        3. Are inferences clearly labeled?
        4. Are citations accurate?
        5. What information is missing?
        
        Provide your critique:
        """
        
        critique = self.llm.generate(prompt, temperature=0.1)
        state["critique"] = critique
        
        if "not enough evidence" in critique.lower() and state["iteration"] < 3:
            state["needs_web_search"] = True
        else:
            state["needs_web_search"] = False
        
        return state
    
    def _should_continue(self, state: ResearchState) -> str:
        """Determine if research should continue."""
        if state.get("needs_web_search", False) and state["iteration"] < 3:
            return "continue"
        return "end"
    
    def _generate_response(self, state: ResearchState) -> ResearchState:
        """Generate final research response."""
        prompt = self._build_response_prompt(state)
        response = self.llm.generate(prompt, temperature=0.1)
        formatted_response = self._format_response(response, state)
        state["response"] = formatted_response
        return state
    
    def _build_response_prompt(self, state: ResearchState) -> str:
        """Build prompt for final response."""
        return f"""Generate a research analysis based on the following:

        Query: {state['query']}

        Paper Analyses:
        {json.dumps(state['paper_analysis'], default=str, indent=2)[:3000]}

        Identified Gaps:
        {json.dumps(state['gaps'], default=str, indent=2)[:2000]}

        Critique:
        {state.get('critique', 'No critique available')}

        Instructions:
        1. Answer the query directly
        2. Cite specific papers and pages for all claims
        3. Distinguish between explicit statements and inferences
        4. Identify common patterns and limitations
        5. Suggest specific research gaps
        6. Provide potential research directions
        7. Be concise but comprehensive

        Format the response with:
        - ## Answer
        - ## Evidence
        - ## Limitations
        - ## Research Gaps
        - ## Future Directions
        - ## Sources
        """
    
    def _format_response(self, response: str, state: ResearchState) -> str:
        """Format final response with proper citations."""
        citations = []
        for chunk in state["retrieved_chunks"][:10]:
            citations.append({
                "paper": chunk["metadata"].get("paper_id", "unknown"),
                "page": chunk["metadata"].get("page_number", "unknown"),
                "text": chunk["text"][:200] + "..."
            })
        
        formatted = response + "\n\n## Sources\n\n"
        for i, citation in enumerate(citations, 1):
            formatted += f"{i}. Paper: {citation['paper']} (Page {citation['page']})\n"
            formatted += f"   {citation['text']}\n\n"
        
        return formatted
    
    def run(self, query: str, thread_id: str = "default") -> Dict[str, Any]:
        """Run the research agent."""
        initial_state = {
            "query": query,
            "papers": [],
            "retrieved_chunks": [],
            "paper_analysis": [],
            "gaps": [],
            "response": "",
            "iteration": 0,
            "needs_web_search": False,
            "query_analysis": "",
            "critique": "",
            "retrieved_at_iteration": 0
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = self.app.invoke(initial_state, config)
        except Exception as e:
            return {
                "query": query,
                "response": f"Error: {str(e)}",
                "gaps": [],
                "paper_analysis": [],
                "citations": [],
                "total_papers": 0,
                "total_chunks": 0
            }
        
        return {
            "query": query,
            "response": result.get("response", "No response generated"),
            "gaps": result.get("gaps", []),
            "paper_analysis": result.get("paper_analysis", []),
            "citations": self._extract_citations(result),
            "total_papers": len(result.get("paper_analysis", [])),
            "total_chunks": len(result.get("retrieved_chunks", []))
        }
    
    def _extract_citations(self, state: ResearchState) -> List[Dict[str, Any]]:
        """Extract citations from research results."""
        citations = []
        for chunk in state.get("retrieved_chunks", [])[:10]:
            citations.append({
                "paper_id": chunk["metadata"].get("paper_id", "unknown"),
                "page": chunk["metadata"].get("page_number", "unknown"),
                "text": chunk["text"][:200] + "..."
            })
        return citations