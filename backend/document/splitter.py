from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..core.config import Config

class DocumentSplitter:
    """Split documents into chunks."""
    
    def __init__(self):
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
    
    def split_document(self, paper: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a document into chunks with metadata."""
        chunks = []
        
        for page in paper["pages"]:
            page_text = page["content"]
            page_number = page["page_number"]
            
            # Split page text into chunks
            page_chunks = self.splitter.split_text(page_text)
            
            for i, chunk_text in enumerate(page_chunks):
                chunk_id = f"{paper['paper_id']}_{page_number}_{i:03d}"
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "paper_id": paper["paper_id"],
                    "file_name": paper["file_name"],
                    "page_number": page_number,
                    "chunk_index": i,
                    "content": chunk_text,
                    "metadata": {
                        "paper_id": paper["paper_id"],
                        "file_name": paper.get("file_name", ""),
                        "file_hash": paper.get("file_hash", ""),
                        "page_number": page_number,
                        "total_pages": paper.get("total_pages", len(paper.get("pages", []))),
                        "chunk_id": chunk_id,
                        "title": paper.get("title", ""),
                        "authors": paper.get("authors", ""),
                        "year": paper.get("year", ""),
                        "indexed_at": paper.get("processed_at", "")
                    }
                })
        
        return chunks