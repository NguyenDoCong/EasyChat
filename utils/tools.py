from typing import List, Dict, Any, Optional, Literal
from .store import build_self_query_retriever
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from .store import build_vector_store
from pydantic import BaseModel
from raw_data import get_data

load_dotenv()
llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    model="google/gemini-2.0-flash-001",
)

class Data(BaseModel):
    href: str

data = []

# vector_store needs to be initialized with tasks data
vector_store = build_vector_store(data)

def store_search(query: str) -> Dict[str, Any]:
    # , filter: Optional[Dict[str, str]] = None
    """
    Search for tasks related to query and return tasks.

    Parameters:
        query (str): User query string.

    Returns:
        Dict[str, Any]: Related tasks.
    """
    print(f"Query: {query}")

    retriever = build_self_query_retriever(llm, vector_store)

    result = retriever.invoke(query)
    # return compressed_docs
    return result
