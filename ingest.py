import os
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1️⃣ Define header-based chunking
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)

def ingest_data():
    print("Loading Markdown documents from /data...")

    docs = []

    for filename in os.listdir("data"):
        if filename.endswith(".md"):
            with open(os.path.join("data", filename), "r", encoding="utf-8") as f:
                text = f.read()

                # Smart header-based splitting
                splits = markdown_splitter.split_text(text)
                docs.extend(splits)

    print(f"Generated {len(docs)} smart chunks.")

    # 2️⃣ Local embedding model (no API cost)
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # 3️⃣ Store in ChromaDB
    print("Vectorizing and storing in ChromaDB...")

    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    print("Ingestion complete. Database saved to ./chroma_db")

if __name__ == "__main__":
    ingest_data()
