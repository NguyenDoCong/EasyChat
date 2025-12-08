from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from uuid import uuid4
from utils.raw_data import get_data
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
import os
from openai import OpenAI
from dataclasses import dataclass
from langchain.agents.structured_output import ToolStrategy
from langchain_core.documents import Document

load_dotenv()

# llm = ChatOpenAI(
#     model="gpt-4o-mini",
# )

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # other params...
# )

llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    model="openai/gpt-oss-20b:free",
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")

# Global variable to store the retriever
current_retriever = None
_initialized = False

# async def initialize_retriever(href: str = None):
async def initialize_retriever(documents: Document = None):
    """Initialize retriever once and reuse"""
    global current_retriever, _initialized
    
    # if _initialized and current_retriever is not None:
    #     return current_retriever
    
    if documents is None:
        raise ValueError("documents is required for first initialization")
    
    # documents = await get_data(href)
    client = QdrantClient(":memory:")
    
    client.create_collection(
        collection_name="demo_collection",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="demo_collection",
        embedding=embeddings,
    )
    
    # uuids = [str(uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents=documents)
    
    current_retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 3})
    _initialized = True
    
    return current_retriever

# def build_retriever(href: str):
#     global current_retriever
#     documents = get_data(href)
#     # # vector_store needs to be initialized with tasks data
#     # vector_store = build_vector_store(data)

#     # retriever = build_self_query_retriever(llm, vector_store)
#     # current_retriever = retriever
#     client = QdrantClient(":memory:")

#     client.create_collection(
#         collection_name="demo_collection",
#         vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
#     )

#     vector_store = QdrantVectorStore(
#         client=client,
#         collection_name="demo_collection",
#         embedding=embeddings,
#     )

#     uuids = [str(uuid4()) for _ in range(len(documents))]

#     vector_store.add_documents(documents=documents, ids=uuids)

#     retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 3})
#     current_retriever = retriever

#     return retriever

# @tool
def store_search(query: str) -> Dict[str, Any]:
    """Search the vector store.

    Args:
        query: User query string
    """
    global current_retriever
    print(f"Query: {query}")
    try:
        if current_retriever is None:
            return {
                "error": "Vector store not initialized. Please call /init endpoint first."
            }
        result = current_retriever.invoke(query)
        # return compressed_docs
        return result
    except Exception as e:
        print(f"Error during store_search: {e}")
        return {"error": str(e)}

# @dataclass
class ProductInfo(BaseModel):
    """Information for a product."""

    url: str = Field(description="The url of the product")
    name: str = Field(description="The name of the product")
    price: str = Field(description="The price of the product")
    specs: str = Field(description="The specifications of the product")
    src: str = Field(description="The image src link of the product")


# Augment the LLM with tools
tools = [store_search]
# tools_by_name = {tool.name: tool for tool in tools}
# model_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a helpful assistant tasked with returning relevant answer based on a set of inputs.
                IMPORTANT: You only need to make 1 store_search tool call, then use the results to extract required information. 
                You can extract url from metadata field in the store_search tool response.
                Always respond with a JSON object matching this structure:
                {
                    "url": "string",
                    "name": "string",
                    "price": "string",
                    "specs": "string",
                    "src": "string"
                }
                """

llm_agent = create_agent(
    llm,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    response_format=ToolStrategy(ProductInfo),  
)



# # Run the agent
# llm_agent.invoke(
#     {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
# )
