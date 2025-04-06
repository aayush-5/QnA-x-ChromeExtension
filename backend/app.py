from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os


from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

model = OllamaLLM(model="llama3.1:8b")

app = FastAPI()

# Enable CORS so frontend (Chrome extension) can access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to your extension's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Define request body schemas
class URLPayload(BaseModel):
    url: str

class QuestionPayload(BaseModel):
    url: str
    question: str

cached_vectorstores = {}

@app.post("/api/send_url")
async def send_url(payload: URLPayload):
    url = payload.url
    print(f"🔗 Received URL: {url}")

    try:
        # Load page
        loader = WebBaseLoader(url)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(docs)

        # Create embeddings and store in FAISS vectorstore
        vectorstore = FAISS.from_documents(splits, embeddings)
        cached_vectorstores[url] = vectorstore


    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}


@app.post("/api/ask_question")
async def ask_question(payload: QuestionPayload):
    url = payload.url
    question = payload.question
    print(f"❓ Question received: '{question}' for {url}")

    try:
        # Check cache
        if url in cached_vectorstores:
            vectorstore = cached_vectorstores[url]
        else:
            # Reload and recreate vectorstore if not cached
            loader = WebBaseLoader(url)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = splitter.split_documents(docs)
            vectorstore = FAISS.from_documents(splits, embeddings)
            cached_vectorstores[url] = vectorstore

        # Run QA
        qa = RetrievalQA.from_chain_type(
            llm=model,
            retriever=vectorstore.as_retriever()
        )

        answer = qa.run(question)
        print(answer)
        return {"answer": answer}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}
