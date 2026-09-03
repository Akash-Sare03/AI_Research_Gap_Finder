# backend/core/llm.py

import re
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ..core.config import Config

class LLMService:
    """Production GenAI & Transformer LLM service using active Groq models with auto-fallback."""
    
    MODELS = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.6-27b"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.default_api_key = api_key or Config.GROQ_API_KEY
        self.model_name = Config.LLM_MODEL or "qwen/qwen3.8-27b"
        self._clients: Dict[str, Any] = {}
    
    def get_client(self, api_key: Optional[str] = None):
        """Lazy load and cache Groq client per API key."""
        active_key = (api_key or self.default_api_key or "").strip()
        if not active_key:
            raise ValueError("No Groq API key configured. Please enter your Groq API key in Settings.")
        
        if active_key not in self._clients:
            try:
                from groq import Groq
                self._clients[active_key] = Groq(api_key=active_key, timeout=25.0)
            except Exception as e:
                raise Exception(f"Failed to initialize Groq client: {str(e)}")
        
        return self._clients[active_key]
    
    def generate(self, prompt: str, temperature: float = 0.2, api_key: Optional[str] = None) -> str:
        """Generate response from the Transformer model with automatic multi-model fallback."""
        active_key = (api_key or self.default_api_key or "").strip()
        if not active_key:
            raise ValueError("No Groq API key available. Please enter your Groq API key to proceed.")
        
        client = self.get_client(active_key)
        models_to_try = [self.model_name] + [m for m in self.MODELS if m != self.model_name]
        last_error = None
        
        for model in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an elite academic research scientist and peer reviewer. "
                                "You provide deeply factual, rigorous, structured, and insightful answers to research questions. "
                                "Explain complex concepts in accessible, clear plain English without robotic boilerplate."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    model=model,
                    temperature=temperature,
                    max_tokens=4096
                )
                if chat_completion and chat_completion.choices:
                    content = chat_completion.choices[0].message.content or ""
                    # Strip reasoning tokens if present
                    clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                    if clean_content:
                        return clean_content
            except Exception as e:
                err_str = str(e)
                last_error = e
                if "401" in err_str or "invalid_api_key" in err_str.lower():
                    raise ValueError("Your Groq API key is invalid or expired. Please update it in Settings.")
                elif "429" in err_str or "rate_limit" in err_str.lower():
                    continue
                continue
        
        # Try LangChain fallback
        try:
            lc_llm = ChatGroq(
                groq_api_key=active_key,
                model_name="qwen/qwen3.8-27b",
                temperature=temperature,
                max_tokens=4096
            )
            messages = [
                SystemMessage(content="You are an AI research analyst analyzing research papers."),
                HumanMessage(content=prompt)
            ]
            res = lc_llm.invoke(messages)
            if res and res.content and res.content.strip():
                clean_res = re.sub(r'<think>.*?</think>', '', res.content, flags=re.DOTALL).strip()
                return clean_res
        except Exception as e:
            last_error = e
        
        err_msg = str(last_error)
        if "429" in err_msg or "rate_limit" in err_msg.lower():
            raise Exception("You have reached your Groq API rate limit. Please wait a moment or update your API key in Settings.")
        
        raise Exception(f"LLM generation failed: {err_msg}")
    
    def generate_with_context(self, context: str, query: str, api_key: Optional[str] = None) -> str:
        """Generate response with context."""
        prompt = f"""You are an AI research analyst. Analyze the following research paper excerpts and answer the query.

## Context from Papers:
{context}

## Query:
{query}

Provide a comprehensive, factual, and deeply structured response."""
        return self.generate(prompt, temperature=0.2, api_key=api_key)
