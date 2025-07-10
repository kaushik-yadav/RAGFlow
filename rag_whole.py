import time

# start timer
start_time = time.time()
import base64
import json
import os
import uuid
from typing import Dict, List

import google.generativeai as genai
import pymupdf4llm
from dotenv import load_dotenv
from groq import Groq
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.schema import Document
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings
from PIL import Image
from unstructured.partition.pdf import partition_pdf

load_dotenv()

# start timer
start_time = time.time()

# Load API keys
groq_api_key = os.getenv('GROQ_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')

genai.configure(api_key=os.getenv("GEMINI_IMAGE_API_KEY"))
assert groq_api_key, 'Set GROQ_API_KEY in .env'
assert COHERE_API_KEY, 'Set COHERE_API_KEY in .env'

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Configuration
COLLECTION_NAME = 'multi_modal_rag'
ID_KEY = 'doc_id'
PROCESSED_FILE = 'processed.json'
MAX_DOCS = 5

# Load ingestion records
if os.path.exists(PROCESSED_FILE):
    raw = json.load(open(PROCESSED_FILE))
    records = raw if isinstance(raw, list) and all(isinstance(r, dict) for r in raw) else []
else:
    records = []

# Embedding function (Cohere)
embedding_function = CohereEmbeddings(
    model='embed-english-v3.0',
    cohere_api_key=COHERE_API_KEY
)

# Vectorstore setup
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory='./chroma_store',
    embedding_function=embedding_function
)

docstore = InMemoryStore()

# Docstore and Retriever
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    id_key=ID_KEY
)

# Image captioning using Groq vision model
def caption_image(image_path: str) -> str:
    cap_time = time.time()
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    image_data_url = f"data:image/png;base64,{image_b64}"
    try:
        completion = client.chat.completions.create(
            model='meta-llama/llama-4-scout-17b-16e-instruct',
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Describe the image in detail along with its components under 150 words.Also mention the connection of components like which component is connected to which.Provide the workflow of diagram'
                        },
                        {
                            'type': 'image_url',
                            'image_url': {'url': image_data_url}
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_completion_tokens=1000,
            top_p=1,
            stream=True
        )
        caption = ''
        for chunk in completion:
            caption += chunk.choices[0].delta.content or ''
        print('Elapsed captioning time', round(time.time() - cap_time, 2), 's')
        return caption.strip()
    except Exception as e:
        print(f"Error captioning image: {e}")
        print('Elapsed captioning time', round(time.time() - cap_time, 2), 's')
        return ''

# PDF + Table extraction
def extract_pdf(path: str) -> Dict[str, List[str]]:
    pdf_time = time.time()
    chunks = partition_pdf(
        filename=path,
        infer_table_structure=True,
        strategy='fast',
        extract_image_block_types=['Image'],
        extract_image_block_to_payload=True,
        chunking_strategy='by_title',
        max_characters=10000,
        combine_text_under_n_chars=2000,
        new_after_n_chars=6000
    )
    texts, tables = [], []
    for c in chunks:
        cls = type(c).__name__
        if cls == 'CompositeElement':
            texts.append(str(c))
        elif cls == 'TableElement':
            tables.append(getattr(c.metadata, 'text_as_html', str(c)))
    print('Elapsed pdf time', round(time.time() - pdf_time, 2), 's')
    return {'texts': texts, 'tables': tables}

# Image extraction
def extract_images(path: str, out_dir: str = 'figures') -> List[Dict]:
    out_dir = os.path.join(out_dir,path.split("/")[1].split(".pdf")[0])
    img_time = time.time()
    os.makedirs(out_dir, exist_ok=True)

    # Clear previous images
    for f in os.listdir(out_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(out_dir, f))

    # Use pymupdf4llm to extract all images
    pymupdf4llm.to_markdown(
        path,
        write_images=True,
        image_path=out_dir,
        image_format='png',
        dpi=300,
        page_chunks=True
    )

    # Infer page and figure number from filenames
    image_records = []
    for fname in sorted(os.listdir(out_dir)):
        if fname.endswith('.png'):
            try:
                # e.g., attention.pdf-2-0.png → page 2, fig 1
                parts = fname.split('-')
                page = int(parts[-2]) + 1
                fig = int(parts[-1].split('.')[0]) + 1
                image_records.append({
                    'path': os.path.join(out_dir, fname),
                    'page': page,
                    'figure': fig,
                    'filename': fname
                })
            except Exception as e:
                print(f"Warning: Could not parse metadata from {fname}: {e}")

    print('Elapsed image time', round(time.time() - img_time, 2), 's')
    return image_records

# Main RAG pipeline
def process(path: str):
    doc_id = str(uuid.uuid4())
    print('Processing', path)
    data = extract_pdf(path)
    imgs = extract_images(path)

    # only image captions now
    img_captions = []
    for i in imgs:
        cap = caption_image(i["path"])
        if cap:
            img_captions.append({
                "content": f"[Figure {i['figure']}, Page {i['page']}]: {cap}",
                "original": i
            })

    # upsert raw text, tables, and image captions
    def upsert_list(contents, originals, kind):
        ids = [str(uuid.uuid4()) for _ in contents]
        if kind == 'image':
            docs = [Document(
                page_content=item["content"],
                metadata={ID_KEY: doc_id, 'type': kind, 'page': item["original"]["page"], 'figure': item["original"]["figure"], 'filename': item["original"]["filename"]}
            ) for item in contents]
            originals = [item["original"] for item in contents]
        else:
            docs = [Document(page_content=content, metadata={ID_KEY: doc_id, 'type': kind}) for content in contents]
        vectorstore.add_documents(docs)
        docstore.mset(list(zip(ids, originals)))

    if data['texts']:
        upsert_list(data['texts'], data['texts'], 'text')
    if data['tables']:
        upsert_list(data['tables'], data['tables'], 'table')
    if img_captions:
        upsert_list(img_captions, imgs, 'image')
    print('-- Added to ChromaDB')

    records.append({'path': path, 'doc_id': doc_id, 'timestamp': time.time()})
    if len(records) > MAX_DOCS:
        oldest = min(records, key=lambda r: r['timestamp'])
        print(f"Evicting oldest: {oldest['path']}")
        vectorstore.delete(filter={ID_KEY: oldest['doc_id']})
        records.remove(oldest)

    json.dump(records, open(PROCESSED_FILE, 'w'), indent=2)
    print('Done', path)

# entry point
if __name__ == '__main__':
    pdf = 'attention.pdf'
    if not os.path.isfile(pdf):
        print('Not found:', pdf)
    else:
        process(pdf)
    print('Elapsed', round(time.time() - start_time, 2), 's')