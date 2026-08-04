import json
import re
import os
import hashlib
import chromadb
from chromadb.utils import embedding_functions


raw_dat_path="ka/data/raw_docs.json"
chroma_path="/kb/chroma/db"
collection_name="business_loan_kb"

chroma_client=chromadb.PersistentClient(path=chroma_path)
embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

header_footer_pattern =r"(--- HEADER:.*?---)|(---FOOTER:.*?---)"
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
phone_pattern = r"\+?\d[\d\s\-()]{8,}\d"
ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"


def clean_text(text: str)->str:
    text= re.sub(header_footer_pattern, "", text, flags=re.DOTALL)
    text= re.sub(r"\n+", "\n", text).strip()
    return text

def detect_ans_mask_pii(text:str)->tuple[str,bool]:
    pii_found=False
    if re.search(email_pattern, text):
        pii_found=True
    if re.search(phone_pattern, text):
        pii_found=True
    if re.search(ssn_pattern, text):
        pii_found=True
    masked_text = re.sub(email_pattern, "[PROTECTED EMAIL]", text)
    masked_text = re.sub(phone_pattern, "[PROTECTED PHONE]", masked_text)
    masked_text = re.sub(ssn_pattern, "[PROTECTED SSN]", masked_text)
    return masked_text, pii_found

def extract_title_and_category(text: str, soure: str)-> tuple[str,str]:
    lines=text.split("\n")
    title="General Business Loan Information"
    for line in lines:
        if line.startswith("##"):
            title=line.replace("##", "").strip()
            break
    title_lower=title.lower()
    title_lower = title.lower()
    if "eligibility" in title_lower or "qualification" in title_lower:
        category = "qualification_rules"
    elif "rate" in title_lower or "interest" in title_lower:
        category = "rates_and_terms"
    elif "payoff" in title_lower or "penalty" in title_lower:
        category = "policy"
    elif "personal" in title_lower or "out-of-scope" in title_lower:
        category = "scope_rules"
    elif "documentation" in title_lower or "required" in title_lower:
        category = "requirements"
    else:
        category = "faq"
        
    return title, category

def run_ingestion():
    print("Starting ingestion...")

    with open(raw_dat_path, "r") as f:
        docs = json.load(f)
    seen_hashes = set()
    cleaned_records=[]
    for idx, doc in enumerate(docs):
        cleaned_text=clean_text(doc["text"])
        content_hash=hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            print(f"Duplicate content found for document {idx}, skipping ingestion.")
            continue
        seen_hashes.add(content_hash)

        masked_text, pii_found=detect_ans_mask_pii(cleaned_text)
        title, category = extract_title_and_category(masked_text, doc["source"])
        record_id=f"kb_product_{idx+1:03d}"

        record={
            "record_id": record_id,
            "title": title,
            "category": category,
            "content": masked_text,
            "source": doc["source"],
            "PII_flag": pii_found,
            "version": 1
        }
        cleaned_records.append(record)

    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection=chroma_client.create_collection(name=collection_name, embedding_function=embedding_function)
    ids=[r["record_id"] for r in cleaned_records]
    documents=[f"Title:{r['title']}\nCategory:{r['category']}\nContent:{r['content']}" for r in cleaned_records]
    metadatas=[{"source": r["source"], "PII_flag": r["PII_flag"], "version": r["version"]} for r in cleaned_records]
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    print(f"Ingestion completed. {len(cleaned_records)} records ingested into ChromaDB collection '{collection_name}'.")

if __name__=="__main__":
    run_ingestion()
