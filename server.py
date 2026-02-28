from fastapi import FastAPI
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

app = FastAPI()

# Load embeddings + DB at startup
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

vector_db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

class QueryRequest(BaseModel):
    question: str

@app.post("/rag/query")
def query_knowledge_base(request: QueryRequest):
    """
    OpenClaw calls this endpoint.
    We return the top 3 most relevant legal chunks.
    """

    results = vector_db.similarity_search(
        request.question,
        k=3
    )

    if not results:
        return {
            "context": "No relevant information found in the official documents."
        }

    context = "\n\n".join([
        f"Excerpt from {doc.metadata.get('Header 1', 'Document')}:\n{doc.page_content}"
        for doc in results
    ])

    return {
        "status": "success",
        "context": context
    }
