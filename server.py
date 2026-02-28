import sqlite3
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

app = FastAPI()

# 1. INITIALIZE DB & RAG (Done at Startup)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

def init_db():
    conn = sqlite3.connect('glow_store.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS orders 
                    (id INTEGER PRIMARY KEY, gateway_order_id TEXT, status TEXT, phone TEXT)''')
    conn.commit()
    conn.close()

init_db()

# 2. MODELS
class QueryRequest(BaseModel):
    question: str

# 3. RAG ENDPOINT (The "Brain")
@app.post("/rag/query")
def query_knowledge_base(request: QueryRequest):
    results = vector_db.similarity_search(request.question, k=3)
    if not results:
        return {"context": "No relevant information found."}
    
    context = "\n\n".join([f"Source: {doc.metadata.get('Header 1', 'Legal')}\n{doc.page_content}" for doc in results])
    return {"status": "success", "context": context}

# 4. WEBHOOK ENDPOINT (The "Bank Confirmation")
@app.post("/payments/webhook")
async def payment_webhook(request: Request):
    # SECURITY: Verify Razorpay Signature (Crucial for high margins like ₹1700)
    raw_body = await request.body()
    # secret = "YOUR_RAZORPAY_WEBHOOK_SECRET"
    # Logic to verify hmac.new(secret, raw_body, hashlib.sha256)...
    
    payload = await request.json()
    
    # Razorpay payload structures are nested; navigate carefully
    try:
        payment_entity = payload['payload']['payment']['entity']
        order_id = payment_entity['order_id']
        event = payload['event']
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid Payload")

    if event == "payment.captured":
        conn = sqlite3.connect('glow_store.db')
        # Update status so the user is marked as 'paid'
        conn.execute("UPDATE orders SET status = 'paid' WHERE gateway_order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        
        # TRIGGER: This is where you call OpenClaw to send the WhatsApp confirmation
        print(f"DEBUG: Triggering OpenClaw confirmation for Order {order_id}")
        
    return {"status": "ok"}