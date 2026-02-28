import os
import psycopg2
from psycopg2.extras import RealDictCursor
import razorpay
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

app = FastAPI()

# --- CONFIGURATION ---
RAZORPAY_KEY_ID = "rzp_test_your_id"
RAZORPAY_KEY_SECRET = "your_secret"
DATABASE_URL = "dbname=cafeglow user=postgres password=yourpassword host=localhost"

# Initialize Razorpay Client
razor_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Initialize RAG
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

def get_db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# --- MODELS ---
class UserOnboard(BaseModel):
    phone: str
    name: str
    skin_type: str
    reminder_time: str # format "HH:MM"

class OrderCreate(BaseModel):
    phone: str
    flavor: str
    amount: int # in INR (e.g., 1700)

class QueryRequest(BaseModel):
    question: str

# --- ENDPOINTS ---

@app.post("/user/onboard")
async def onboard_user(user: UserOnboard):
    """Saves the user profile and consultation details."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (phone, name, skin_type, reminder_time) VALUES (%s, %s, %s, %s) ON CONFLICT (phone) DO UPDATE SET name=%s, skin_type=%s, reminder_time=%s",
        (user.phone, user.name, user.skin_type, user.reminder_time, user.name, user.skin_type, user.reminder_time)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": "User profile created."}

@app.post("/order/create")
async def create_purchase_order(order: OrderCreate):
    """Creates a real Razorpay order and saves to Postgres."""
    # Razorpay expects amount in paise (1700 INR = 170000 paise)
    amount_paise = order.amount * 100
    razor_order = razor_client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    conn = get_db_conn()
    cur = conn.cursor()
    # Link the order to the user via phone
    cur.execute("SELECT id FROM users WHERE phone = %s", (order.phone,))
    user = cur.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Onboard first.")

    cur.execute(
        "INSERT INTO orders (user_id, gateway_order_id, product_flavor, amount_paise, status) VALUES (%s, %s, %s, %s, %s)",
        (user['id'], razor_order['id'], order.flavor, amount_paise, 'pending')
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"order_id": razor_order['id'], "amount": order.amount}

@app.post("/rag/query")
def query_knowledge_base(request: QueryRequest):
    """Standard RAG lookup for FSSAI/T&C facts."""
    results = vector_db.similarity_search(request.question, k=3)
    if not results:
        return {"context": "No relevant info found."}
    context = "\n\n".join([f"Source: {doc.metadata.get('Header 1', 'Legal')}\n{doc.page_content}" for doc in results])
    return {"status": "success", "context": context}

@app.post("/payments/webhook")
async def payment_webhook(request: Request):
    """Finalizes the sale when Razorpay confirms the money is captured."""
    payload = await request.json()
    
    # In production, verify the signature here for security
    event = payload.get('event')
    
    if event == "payment.captured":
        order_id = payload['payload']['payment']['entity']['order_id']
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = 'paid' WHERE gateway_order_id = %s", (order_id,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"ORDER {order_id} MARKED AS PAID. Triggering OpenClaw notification.")

    return {"status": "ok"}