"""
Regulatory RAG Engine for NutriPure AI.
Ingests FSSAI Gazette PDFs and WHO standards into ChromaDB,
providing semantic search for food law compliance and deceptive marketing detection.
"""

import os
import glob
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RegulatoryRAG:
    """Vector database and semantic search engine over official food safety laws."""

    def __init__(
        self,
        persist_dir: str = "data/chroma_db",
        collection_name: str = "food_regulations"
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Initialize persistent ChromaDB client
        os.makedirs(self.persist_dir, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Use lightweight local embedding function (SentenceTransformer / Chroma default)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "FSSAI and WHO legal food regulations"}
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=120,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )

    def load_markdown_docs(self, docs_dir: str = "data/regulatory_docs") -> List[Dict]:
        """Loads and splits all Markdown regulatory documents."""
        documents = []
        md_files = glob.glob(os.path.join(docs_dir, "*.md"))
        
        for file_path in md_files:
            file_name = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            chunks = self.text_splitter.split_text(content)
            for idx, chunk in enumerate(chunks):
                documents.append({
                    "id": f"md_{file_name}_{idx}",
                    "text": chunk,
                    "metadata": {
                        "source": file_name,
                        "doc_type": "markdown_codex",
                        "chunk_index": idx
                    }
                })
        return documents

    def load_pdf_docs(self, docs_dir: str = "data/regulatory_docs") -> List[Dict]:
        """Extracts text page-by-page from official government PDFs using pypdf."""
        documents = []
        pdf_files = glob.glob(os.path.join(docs_dir, "*.pdf"))
        
        for file_path in pdf_files:
            file_name = os.path.basename(file_path)
            reader = PdfReader(file_path)
            
            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if not page_text or not page_text.strip():
                    continue
                    
                chunks = self.text_splitter.split_text(page_text)
                for chunk_idx, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"pdf_{file_name}_p{page_idx}_{chunk_idx}",
                        "text": chunk,
                        "metadata": {
                            "source": file_name,
                            "doc_type": "official_gazette_pdf",
                            "page_number": page_idx,
                            "chunk_index": chunk_idx
                        }
                    })
        return documents

    def build_index(self, force_reload: bool = False) -> int:
        """Indexes all regulatory documents into ChromaDB. Skips if already populated."""
        current_count = self.collection.count()
        if current_count > 0 and not force_reload:
            return current_count
            
        if force_reload and current_count > 0:
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )

        # Ingest both Markdown and PDF documents
        all_docs = self.load_markdown_docs() + self.load_pdf_docs()
        
        if not all_docs:
            return 0
            
        # Batch insert into ChromaDB
        batch_size = 100
        for i in range(0, len(all_docs), batch_size):
            batch = all_docs[i:i + batch_size]
            self.collection.add(
                ids=[doc["id"] for doc in batch],
                documents=[doc["text"] for doc in batch],
                metadatas=[doc["metadata"] for doc in batch]
            )
            
        return self.collection.count()

    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """
        Performs semantic similarity search for a given food claim or question.
        Returns top-k matching regulatory chunks with source and page citations.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        formatted_results = []
        if not results or not results["documents"] or not results["documents"][0]:
            return formatted_results
            
        for i in range(len(results["documents"][0])):
            doc_text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i] if "distances" in results and results["distances"] else None
            
            # Format citation string
            page_info = f", Page {metadata['page_number']}" if "page_number" in metadata else ""
            citation = f"{metadata['source']}{page_info}"
            
            formatted_results.append({
                "text": doc_text,
                "citation": citation,
                "metadata": metadata,
                "distance": distance
            })
            
        return formatted_results

    def verify_marketing_claim(self, claim: str, ingredient_details: str) -> Dict:
        """
        Targeted compliance query that pairs a front marketing claim with back ingredient reality.
        Returns relevant legal standards and citations.
        """
        search_prompt = f"Claim '{claim}' regulations legality threshold ingredients: {ingredient_details}"
        matched_chunks = self.query(search_prompt, n_results=2)
        
        return {
            "claim": claim,
            "relevant_clauses": [m["text"] for m in matched_chunks],
            "citations": [m["citation"] for m in matched_chunks]
        }
