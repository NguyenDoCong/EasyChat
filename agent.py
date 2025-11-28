from langchain_openai import ChatOpenAI
from langchain.tools import tool
import os
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Literal
from langgraph.graph import StateGraph, START, END
from typing import Dict, Any
from pydantic import BaseModel, Field
from utils.raw_data import get_data
import logging
import getpass
from dotenv import load_dotenv
from openai import OpenAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_ollama import OllamaEmbeddings
from uuid import uuid4
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# llm = ChatOpenAI(
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     base_url=os.getenv("OPENROUTER_BASE_URL"),
#     model="openai/gpt-oss-20b:free",
# )

# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=os.getenv("OPENROUTER_API_KEY"),
# )

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")

# completion = client.chat.completions.create(
#   model="openai/gpt-4o",
#   messages=[
#     {
#       "role": "user",
#       "content": "What is the meaning of life?"
#     }
#   ]
# )

# print(completion.choices[0].message.content)


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

# llm = ChatOpenAI(
#     model="gpt-4o-mini",
# )


class Data(BaseModel):
    href: str


# Global variable to store the retriever
current_retriever = None


def build_retriever(href: str):
    global current_retriever
    documents = get_data(href)
    # # vector_store needs to be initialized with tasks data
    # vector_store = build_vector_store(data)

    # retriever = build_self_query_retriever(llm, vector_store)
    # current_retriever = retriever
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

    uuids = [str(uuid4()) for _ in range(len(documents))]

    vector_store.add_documents(documents=documents, ids=uuids)

    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 3})
    current_retriever = retriever

    return retriever


# retriever = build_retriever("https://rangdong.com.vn/category/den-led-chieu-sang")


@tool
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
    
class ContactInfo(BaseModel):
    """Information for a product."""

    url: str = Field(description="The url of the product")
    name: str = Field(description="The name of the product")
    price: str = Field(description="The price of the product")
    specs: str = Field(description="The specifications of the product")
    src: str = Field(description="The image src link of the product")

# Augment the LLM with tools
tools = [store_search]
tools_by_name = {tool.name: tool for tool in tools}
# model_with_tools = llm.bind_tools(tools)

llm_agent = create_agent(
    llm,
    tools=tools,    
    response_format=ContactInfo,  # Auto-selects ProviderStrategy
)

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    logger.info("llm_call node invoked")
    try:
        logger.info(f"Current message count: {len(state.get('messages', []))}")
        response_dict = llm_agent.invoke(
            {
                "messages": [
                    SystemMessage(
                        content="""You are a helpful assistant tasked with returning relevant answer based on a set of inputs.
                        IMPORTANT: You only need to make 1 store_search tool call, then use the results to extract required information.
                        """
                    )
                ]
                + state["messages"]
            }
        )
        logger.info(f"LLM response type: {type(response_dict).__name__}")
        # Extract the last message from the response
        response = response_dict["messages"][-1] if isinstance(response_dict, dict) else response_dict
        logger.info(f"Response message type: {type(response).__name__}")
        if hasattr(response, "tool_calls"):
            logger.info(f"Tool calls detected: {len(response.tool_calls)}")

        return {"messages": [response], "llm_calls": state.get("llm_calls", 0) + 1}
    except Exception as e:
        logger.error(f"Error in llm_call: {str(e)}", exc_info=True)
        raise


def tool_node(state: dict):
    """Performs the tool call"""
    logger.info("tool_node invoked")
    try:
        result = []
        last_message = state["messages"][-1]
        logger.info(f"Last message type: {type(last_message).__name__}")
        logger.info(f"Tool calls in message: {len(last_message.tool_calls)}")

        for tool_call in last_message.tool_calls:
            logger.info(f"Executing tool: {tool_call['name']}")
            tool = tools_by_name[tool_call["name"]]
            logger.info(f"Tool found: {tool}")
            logger.info(f"Tool args: {tool_call['args']}")

            observation = tool.invoke(
                tool_call["args"] if isinstance(tool_call["args"], dict) else {}
            )
            logger.info(f"Tool result type: {type(observation).__name__}")
            result.append(
                ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
            )

        logger.info(f"Tool node completed, messages returned: {len(result)}")
        return {"messages": result}
    except Exception as e:
        logger.error(f"Error in tool_node: {str(e)}", exc_info=True)
        raise


def should_continue(state: MessagesState) -> Literal["tool_node", "END"]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return "END"


# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call", should_continue, {"tool_node": "tool_node", "END": END}
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# # Invoke
# messages = [HumanMessage(content="Add 3 and 4.")]
# messages = agent.invoke({"messages": messages})
# for m in messages["messages"]:
#     m.pretty_print()
