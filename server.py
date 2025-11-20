import re
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from utils.crawl import crawl
from pydantic import BaseModel
import uvicorn
from utils.url_validator import filter_valid_urls
from concurrent.futures import ThreadPoolExecutor
from utils.store import build_vector_store
from utils.store import build_self_query_retriever
from typing import Any, Dict
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.documents import Document
import pprint

load_dotenv()

model = ChatOpenAI(
  api_key=os.getenv("OPENROUTER_API_KEY"),
  base_url=os.getenv("OPENROUTER_BASE_URL"),
  model="google/gemini-2.0-flash-001",
)

# Source - https://stackoverflow.com/a
# Posted by Mark Seagoe
# Retrieved 2025-11-20, License - CC BY-SA 4.0

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

def validate_and_sanitize_input(
    question: str, instruction: str = ""
) -> tuple[str, str]:
    """Validate and sanitize user inputs for safety."""
    if len(question) > 1000:
        raise ValueError("Question must be 1000 characters or less")

    if len(instruction) > 2000:
        raise ValueError("Instruction must be 2000 characters or less")

    if not question.strip():
        raise ValueError("Question cannot be empty")

    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    combined_text = f"{question} {instruction}".lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, combined_text, re.IGNORECASE):
            raise ValueError("Input contains potentially unsafe content")

    question = question.replace("<", "&lt;").replace(">", "&gt;")
    instruction = instruction.replace("<", "&lt;").replace(">", "&gt;")

    return question.strip(), instruction.strip()

def store_search(query: str, vector_store: Any) -> Dict[str, Any]:
    # , filter: Optional[Dict[str, str]] = None
    """
    Search for tasks related to query and return tasks.

    Parameters:
        query (str): User query string.

    Returns:
        Dict[str, Any]: Related tasks.
    """
    print(f"Query: {query}")

    retriever = build_self_query_retriever(model, vector_store)

    result = retriever.invoke(query)
    # return compressed_docs
    return result

class Data(BaseModel):
    href: str

@app.post("/hover")
def receive_hover(data: Data):
    print("User hovered:", data.href)
    print("Crawling data...")
    crawled_data = crawl(data.href)
    clean = re.sub(r"<think>.*?</think>", "", crawled_data, flags=re.DOTALL).strip()

    print(clean)
    return {"result": clean}

@app.post("/crawl")
def crawl_url(data: Data):
    try:
        url, content, links = crawl(data.href)
        print(f"Crawled {url}: {len(content)} characters, {len(links)} links")
        valid_links = filter_valid_urls(links, [data.href])
        with ThreadPoolExecutor(max_workers=500) as executor:
            results = executor.map(crawl, valid_links[:100])

        documents = []

        for result in results:
            print("-------------------")
            print(f"url:{result[0]}")  
            print(f"content:{result[1][:50]}")  
            document = Document(page_content=result[1], metadata={"source": result[0]})
            documents.append(document)

        vector_store = build_vector_store(documents)
        retriever = build_self_query_retriever(model, vector_store)
        data = retriever.invoke("Liệt kê các loại bóng đèn")

        pprint.pprint(data)

    except Exception as e:
        print({str(e)})
        raise HTTPException(status_code=500, detail=str(e))    

@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Serve the main configuration page."""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/chatbot", response_class=HTMLResponse)
async def get_chatbot(request: Request):
    """Serve the chatbot page."""
    with open("static/chatbot.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/embed/chatbot.js", response_class=HTMLResponse)
async def get_chatbot_js(request: Request):
    """Serve the chatbot JavaScript for embedding."""
    with open("static/chatbot.js", "r") as f:
        content = f.read()
    return HTMLResponse(
        content=content, headers={"Content-Type": "application/javascript"}
    )


# class ConnectionManager:
#     """Manages WebSocket connections and their associated conversational state."""

#     def __init__(self):
#         self.active_connections: Dict[WebSocket, Dict] = {}
#         self.flows: Dict[WebSocket, Flow] = {}

#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections[websocket] = {}
#         self.flows[websocket] = create_support_bot_flow()
#         print("Client connected")

#     def disconnect(self, websocket: WebSocket):
#         if websocket in self.active_connections:
#             del self.active_connections[websocket]
#         if websocket in self.flows:
#             del self.flows[websocket]
#         print("Client disconnected")

#     def get_shared_state(self, websocket: WebSocket) -> Dict:
#         return self.active_connections.get(websocket)

#     def set_shared_state(self, websocket: WebSocket, state: Dict):
#         self.active_connections[websocket] = state

#     def get_flow(self, websocket: WebSocket) -> Flow:
#         return self.flows.get(websocket)


# manager = ConnectionManager()


# @app.websocket("/api/ws/chat")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             message = json.loads(data)

#             msg_type = message.get("type")
#             payload = message.get("payload", {})

#             try:
#                 question = payload.get("question")
#                 if not question:
#                     raise ValueError("Question is missing.")
#                 question, _ = validate_and_sanitize_input(question)
#             except ValueError as e:
#                 await websocket.send_text(
#                     json.dumps({"type": "error", "payload": str(e)})
#                 )
#                 continue

#             shared_state = manager.get_shared_state(websocket)
#             support_bot_flow = manager.get_flow(websocket)

#             if msg_type == "start" or not shared_state:
#                 current_url = payload.get("current_url", "")
#                 extra_urls = payload.get("extra_urls", [])
#                 instruction = payload.get("instruction", "")
#                 prefixes = payload.get("prefixes", [])

#                 # Limit extra_urls to maximum 10
#                 if len(extra_urls) > 10:
#                     extra_urls = extra_urls[:10]

#                 # Limit prefixes to maximum 10
#                 if len(prefixes) > 10:
#                     prefixes = prefixes[:10]

#                 # If current_url is empty, use the current page URL (this would be handled by frontend)
#                 # Combine current_url and extra_urls into start_urls, removing duplicates
#                 start_urls = []
#                 if current_url:
#                     start_urls.append(current_url)
#                 start_urls.extend(extra_urls)

#                 # Remove duplicates while preserving order
#                 start_urls = list(dict.fromkeys(start_urls))

#                 if not start_urls:
#                     await websocket.send_text(
#                         json.dumps(
#                             {
#                                 "type": "error",
#                                 "payload": "At least one URL (current or extra) is required.",
#                             }
#                         )
#                     )
#                     continue

#                 shared_state = {
#                     "conversation_history": [],
#                     "instruction": instruction,
#                     "allowed_domains": prefixes,
#                     "max_iterations": 5,
#                     "max_pages": 50,
#                     "content_max_chars": 10000,
#                     "max_urls_per_iteration": 5,
#                     "all_discovered_urls": start_urls.copy(),
#                     "visited_urls": set(),
#                     "url_content": {},
#                     "url_graph": {},
#                     "urls_to_process": list(range(len(start_urls))),
#                 }

#             shared_state["user_question"] = question
#             shared_state["current_iteration"] = 0
#             shared_state["final_answer"] = None

#             q = asyncio.Queue()
#             shared_state["progress_queue"] = q

#             def run_sync_flow_in_thread():
#                 try:
#                     support_bot_flow.run(shared_state)
#                     final_answer = shared_state.get("final_answer")
#                     if final_answer:
#                         useful_indices = shared_state.get("useful_visited_indices", [])
#                         useful_pages = [
#                             shared_state["all_discovered_urls"][idx]
#                             for idx in useful_indices
#                             if idx < len(shared_state["all_discovered_urls"])
#                         ]
#                         answer_data = {
#                             "answer": final_answer,
#                             "useful_pages": useful_pages,
#                         }
#                         q.put_nowait(f"FINAL_ANSWER:::{json.dumps(answer_data)}")
#                     else:
#                         q.put_nowait(
#                             "ERROR:::Flow finished, but no answer was generated."
#                         )
#                 except Exception as e:
#                     import traceback

#                     traceback.print_exc()
#                     q.put_nowait(f"ERROR:::An unexpected error occurred: {str(e)}")
#                 finally:
#                     q.put_nowait(None)

#             asyncio.create_task(asyncio.to_thread(run_sync_flow_in_thread))

#             while True:
#                 progress_msg = await q.get()
#                 if progress_msg is None:
#                     break

#                 event_data = {}
#                 if progress_msg.startswith("FINAL_ANSWER:::"):
#                     answer_data = json.loads(
#                         progress_msg.replace("FINAL_ANSWER:::", "", 1)
#                     )
#                     event_data = {
#                         "type": "final_answer",
#                         "payload": answer_data["answer"],
#                         "useful_pages": answer_data["useful_pages"],
#                     }
#                 elif progress_msg.startswith("ERROR:::"):
#                     event_data = {
#                         "type": "error",
#                         "payload": progress_msg.replace("ERROR:::", "", 1),
#                     }
#                 else:
#                     event_data = {"type": "progress", "payload": progress_msg}
#                 await websocket.send_text(json.dumps(event_data))

#             if shared_state.get("final_answer"):
#                 shared_state["conversation_history"].append(
#                     {
#                         "user": shared_state["user_question"],
#                         "bot": shared_state["final_answer"],
#                     }
#                 )
#             shared_state["urls_to_process"] = []

#             manager.set_shared_state(websocket, shared_state)

#     except WebSocketDisconnect:
#         manager.disconnect(websocket)


if __name__ == "__main__":

    

    uvicorn.run(app, host="0.0.0.0", port=8000)
