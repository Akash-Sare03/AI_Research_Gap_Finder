from typing import Dict, Any, List, Optional
try:
    import pypdf as PyPDF2
except ImportError:
    import PyPDF2
import hashlib
import os
from pathlib import Path
import json
from datetime import datetime
from ..core.config import Config

class DocumentLoader:
    """Load and process PDF documents."""
    
    def __init__(self):
        self.upload_dir = Config.UPLOAD_DIR
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        self._metadata_cache = {}
        
    def load_pdf(self, file_path: str) -> Dict[str, Any]:
        """Load a PDF and extract text and metadata."""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # Extract metadata
                metadata = reader.metadata or {}
                
                # Extract text from each page
                pages = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty pages
                        pages.append({
                            "page_number": i + 1,
                            "content": text,
                            "metadata": {
                                "page": i + 1
                            }
                        })
                
                # Compute file hash for change detection
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Get paper info
                file_name = os.path.basename(file_path)
                paper_id = self._generate_paper_id(file_name)
                
                return {
                    "paper_id": paper_id,
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_hash": file_hash,
                    "title": metadata.get("/Title", file_name.replace(".pdf", "")),
                    "authors": metadata.get("/Author", ""),
                    "year": metadata.get("/CreationDate", ""),
                    "pages": pages,
                    "total_pages": len(pages),
                    "processed_at": datetime.now().isoformat()
                }
        except Exception as e:
            raise Exception(f"Failed to load PDF {file_path}: {str(e)}")
    
    def _generate_paper_id(self, file_name: str) -> str:
        """Generate a stable paper ID."""
        base = file_name.replace(".pdf", "").lower()
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        return base
    
    def get_file_hash(self, file_path: str) -> str:
        """Compute file hash for change detection."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()