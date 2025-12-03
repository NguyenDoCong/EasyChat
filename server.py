import re
import logging
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from utils.crawl import crawl
from pydantic import BaseModel
import uvicorn

# from agent import agent_builder, build_retriever
from chain import initialize_retriever
from langchain_core.messages import HumanMessage
import asyncio
from typing import Dict
import json
from chain import llm_agent
from agent import agent_builder
from ddgs import DDGS
from openai import OpenAI
from langchain_openai import ChatOpenAI
import os
from utils.web_crawler import crawl_webpage
from google import genai


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


# async def generate_route(message: str):
#     graph = agent_builder.compile()
#     graph.name = "LangGraphDeployDemo"
#     thread_id = "3"
#     config = {"configurable": {"thread_id": thread_id}}
#     try:
#         result = await graph.ainvoke({"messages": [{"role": "user", "content": {message}}]}, config)
#         message = result["messages"][-1]
#         return message.output_text
#     except Exception as e:
#         print(e)
#         return "Error occurred, please try again later."


class Data(BaseModel):
    message: str


class Info(BaseModel):
    href: str


@app.post("/hover")
def receive_hover(data: Data):
    logger.info(f"User hovered: {data.href}")
    try:
        logger.info("Crawling data...")
        crawled_data = crawl(data.href)
        logger.info(f"Crawl successful, data length: {len(crawled_data)}")
        clean = re.sub(r"<think>.*?</think>", "", crawled_data, flags=re.DOTALL).strip()
        logger.info(f"Cleaned data length: {len(clean)}")
        return {"result": clean}
    except Exception as e:
        logger.error(f"Error in /hover endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/init")
async def create_store(info: Info):
    """Build vector store."""
    logger.info(f"Initializing vector store for URL: {info.href}")
    try:
        await initialize_retriever(info.href)
        logger.info("Vector store initialized successfully")
        return {"message": "Vector store created successfully."}
    except Exception as e:
        logger.error(f"Error in /init endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ExtractedInfos(BaseModel):
    price: str
    specs: str


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

client = genai.Client()


@app.post("/crawl")
async def crawl_url(data: Data):
    logger.info(f"Received crawl request for URL: {data.message}")
    try:
        results = DDGS().text(
            f"{data.message} site:https://rangdong.com.vn/", max_results=5
        )

        selected_urls = []

        for result in results:
            # completion = client.chat.completions.create(
            #     model="openai/gpt-oss-20b:free",
            #     messages=[
            #         {
            #             "role": "user",
            #             "content": f"Is {result['title']} related to {data.message}? Only return 'yes' or 'no'.",
            #         }
            #     ],
            # )

            # # chọn ra các url liên quan tới từ khoá
            # response = client.models.generate_content(
            #     model="gemini-2.0-flash",
            #     contents=f"Is {result['title']} related to {data.message}? Only return 'yes' or 'no'.",
            # )

            # print(completion.choices[0].message.content)
            # if "yes" in completion.choices[0].message.content.lower():
            #     selected_urls.append(result["href"])

            if re.search(re.escape(data.message), result["title"], re.IGNORECASE):
                selected_urls.append(result)

            # print(response.text)
            # if "yes" in response.text.lower():
            #     selected_urls.append(result["href"])

        # crawled_pages = []

        products = []

        for url in selected_urls:
            print(f"Selected URL: {url['href']}")
            link, clean_text, links, image = await crawl_webpage(url["href"])

            if re.search("giá", clean_text, re.IGNORECASE):
            
                name = url["title"]
                # crawled_pages.append((page_data))
                # s = ''.join(clean_text)
                s = clean_text[:10000]  # Giới hạn độ dài văn bản đầu vào

                # response = client.responses.parse(
                #     model="openai/gpt-oss-20b:free",
                #     input=[
                #         {"role": "system", "content": "Extract the product information."},
                #         {
                #             "role": "user",
                #             "content": s,
                #         },
                #     ],
                #     text_format=ExtractedInfos,
                # )

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"Extract the product information from the following text:\n {clean_text}",
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": ExtractedInfos.model_json_schema(),
                    },
                )

                # infos = response.output_parsed
                infos = ExtractedInfos.model_validate_json(response.text)

                # for i, m in enumerate(result["messages"]):
                #     logger.debug(f"Message {i}: {type(m).__name__}")
                #     m.pretty_print()

                # # Extract the last message content
                # last_message = result["messages"][-1]
                # logger.info(f"Last message type: {type(last_message).__name__}")

                # response_content = getattr(last_message, "content", str(last_message))
                # # json_content = json.loads(response_content)
                # # print("Response Content:", json_content)
                # pattern = r"(\w+)\s*=\s*'([^']*)'"
                # result = dict(re.findall(pattern, response_content))

                # if not re.search("N/A", infos.price, re.IGNORECASE):
        
                products.append({
                            "name": name,
                            "price": infos.price,
                            "specs": infos.specs,
                            "link": link,
                            "image": image
                        })

        return {
            "status": "success",
            "type": "products",
            "data": products
        }

    except Exception as e:
        logger.error(f"Error in /crawl endpoint: {str(e)}", exc_info=True)
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


class ConnectionManager:
    """Manages WebSocket connections and their associated conversational state."""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict] = {}
        # self.flows: Dict[WebSocket, Flow] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = {}
        # self.flows[websocket] = create_support_bot_flow()
        print("Client connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        if websocket in self.flows:
            del self.flows[websocket]
        print("Client disconnected")

    def get_shared_state(self, websocket: WebSocket) -> Dict:
        return self.active_connections.get(websocket)

    def set_shared_state(self, websocket: WebSocket, state: Dict):
        self.active_connections[websocket] = state

    # def get_flow(self, websocket: WebSocket) -> Flow:
    #     return self.flows.get(websocket)


manager = ConnectionManager()


@app.websocket("/api/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            payload = message.get("payload", {})

            try:
                question = payload.get("question")
                if not question:
                    raise ValueError("Question is missing.")
                question, _ = validate_and_sanitize_input(question)
            except ValueError as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "payload": str(e)})
                )
                continue

            shared_state = manager.get_shared_state(websocket)
            # support_bot_flow = manager.get_flow(websocket)

            if msg_type == "start" or not shared_state:
                current_url = payload.get("current_url", "")
                extra_urls = payload.get("extra_urls", [])
                instruction = payload.get("instruction", "")
                prefixes = payload.get("prefixes", [])

                # Limit extra_urls to maximum 10
                if len(extra_urls) > 10:
                    extra_urls = extra_urls[:10]

                # Limit prefixes to maximum 10
                if len(prefixes) > 10:
                    prefixes = prefixes[:10]

                # If current_url is empty, use the current page URL (this would be handled by frontend)
                # Combine current_url and extra_urls into start_urls, removing duplicates
                start_urls = []
                if current_url:
                    start_urls.append(current_url)
                start_urls.extend(extra_urls)

                # Remove duplicates while preserving order
                start_urls = list(dict.fromkeys(start_urls))

                if not start_urls:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "payload": "At least one URL (current or extra) is required.",
                            }
                        )
                    )
                    continue

                shared_state = {
                    "conversation_history": [],
                    "instruction": instruction,
                    "allowed_domains": prefixes,
                    "max_iterations": 5,
                    "max_pages": 50,
                    "content_max_chars": 10000,
                    "max_urls_per_iteration": 5,
                    "all_discovered_urls": start_urls.copy(),
                    "visited_urls": set(),
                    "url_content": {},
                    "url_graph": {},
                    "urls_to_process": list(range(len(start_urls))),
                }

            shared_state["user_question"] = question
            shared_state["current_iteration"] = 0
            shared_state["final_answer"] = None

            q = asyncio.Queue()
            shared_state["progress_queue"] = q

            def run_sync_flow_in_thread():
                try:
                    # support_bot_flow.run(shared_state)
                    final_answer = shared_state.get("final_answer")
                    if final_answer:
                        useful_indices = shared_state.get("useful_visited_indices", [])
                        useful_pages = [
                            shared_state["all_discovered_urls"][idx]
                            for idx in useful_indices
                            if idx < len(shared_state["all_discovered_urls"])
                        ]
                        answer_data = {
                            "answer": final_answer,
                            "useful_pages": useful_pages,
                        }
                        q.put_nowait(f"FINAL_ANSWER:::{json.dumps(answer_data)}")
                    else:
                        q.put_nowait(
                            "ERROR:::Flow finished, but no answer was generated."
                        )
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    q.put_nowait(f"ERROR:::An unexpected error occurred: {str(e)}")
                finally:
                    q.put_nowait(None)

            asyncio.create_task(asyncio.to_thread(run_sync_flow_in_thread))

            while True:
                progress_msg = await q.get()
                if progress_msg is None:
                    break

                event_data = {}
                if progress_msg.startswith("FINAL_ANSWER:::"):
                    answer_data = json.loads(
                        progress_msg.replace("FINAL_ANSWER:::", "", 1)
                    )
                    event_data = {
                        "type": "final_answer",
                        "payload": answer_data["answer"],
                        "useful_pages": answer_data["useful_pages"],
                    }
                elif progress_msg.startswith("ERROR:::"):
                    event_data = {
                        "type": "error",
                        "payload": progress_msg.replace("ERROR:::", "", 1),
                    }
                else:
                    event_data = {"type": "progress", "payload": progress_msg}
                await websocket.send_text(json.dumps(event_data))

            if shared_state.get("final_answer"):
                shared_state["conversation_history"].append(
                    {
                        "user": shared_state["user_question"],
                        "bot": shared_state["final_answer"],
                    }
                )
            shared_state["urls_to_process"] = []

            manager.set_shared_state(websocket, shared_state)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
