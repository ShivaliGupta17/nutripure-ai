import sys
import importlib.metadata
import chromadb
import pydantic
import streamlit
import google.genai
import langgraph.graph

print("[OK] Python Version:", sys.version.split()[0])
print("[OK] LangGraph Version:", importlib.metadata.version("langgraph"))
print("[OK] ChromaDB Version:", chromadb.__version__)
print("[OK] Pydantic Version:", pydantic.__version__)
print("[OK] Streamlit Version:", streamlit.__version__)
print("[SUCCESS] All core dependencies verified and functional!")
