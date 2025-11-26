from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")


class AttributeInfo(BaseModel):
    """Information about a metadata attribute for filtering."""
    name: str = Field(..., description="The name of the attribute")
    description: str = Field(..., description="Description of the attribute")
    type: str = Field(default="string", description="The data type of the attribute")


def build_metadata_field_info() -> List[AttributeInfo]:
    """Build metadata field information for filtering."""
    return [
        AttributeInfo(
            name="project name",
            description="The name of the project that the work item belongs to",
            type="string",
        ),
        AttributeInfo(
            name="priority",
            description="The priority of the work item. One of ['urgent', 'high', 'medium', 'low', 'none'], from highest to lowest",
            type="string",
        ),
        AttributeInfo(
            name="state",
            description="The state of the work item. It can take one of the following values:'Todo', 'In Progress', 'Done', 'Backlog', 'Cancelled'",
            type="string",
        ),
        AttributeInfo(
            name="target date",
            description="The due date of the task, in the format YYYY-MM-DD. If the task does not have a due date, the value is None",
            type="float",
        ),
    ]


def build_vector_store(docs: List[Document]) -> Chroma:
    """Build a Chroma vector store from documents."""
    return Chroma.from_documents(docs, embeddings)


def build_self_query_retriever(llm, vector_store: Chroma, examples: Optional[List] = None):
    """
    Build a retriever for the vector store.
    
    In LangChain 1.x, self-query retrievers require langchain-experimental.
    For now, we provide a simplified similarity search retriever.
    
    Args:
        llm: Language model to use
        vector_store: Chroma vector store
        examples: Optional examples for query construction
        
    Returns:
        A retriever for the vector store
    """
    # In LangChain 1.x, return a basic retriever
    # The self-query functionality would require langchain-experimental
    # For now, use the simpler as_retriever approach
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
