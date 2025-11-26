from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_ollama import OllamaEmbeddings
from uuid import uuid4
from raw_data import get_data

embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")

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

documents = get_data("https://rangdong.com.vn/category/den-led-chieu-sang")

uuids = [str(uuid4()) for _ in range(len(documents))]

vector_store.add_documents(documents=documents, ids=uuids)

retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 3})
retriever.invoke("Stealing from the bank is a crime")


