# fastapi/rag/build_index_langchain.py
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd, os, re

STORE = "faiss_store"  # 기존 폴더 재사용

def norm(s): return re.sub(r"\s+", " ", (s or "").strip())
def to_doc(r):
    return Document(
        page_content=f"제목: {norm(r['title'])}\n재료: {norm(r['ingredients'])}\n조리법: {norm(r['content'])}",
        metadata={"title": r["title"], "ingredients": r["ingredients"]}
    )

df = pd.read_csv("data/recipes.csv")
docs = [to_doc(r) for _, r in df.iterrows()]
splits = RecursiveCharacterTextSplitter(chunk_size=550, chunk_overlap=80).split_documents(docs)

emb = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large",
                            encode_kwargs={"normalize_embeddings": True})
vdb = FAISS.from_documents(splits, emb)
vdb.save_local(STORE)
print("✅ RAG index saved at:", STORE)
