import base64
import json
import os
import time
import uuid
from typing import Dict, List

import pymupdf4llm
from dotenv import load_dotenv
from groq import Groq
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.schema import Document
from langchain.storage import InMemoryStore
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma
from unstructured.partition.pdf import partition_pdf

# start timer
start_time = time.time()

# Load API keys
groq_api_key = os.getenv('GROQ_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
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
                            'text': 'Describe the image in detail along with its components under 150 words.'
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
        return caption.strip()
    except Exception as e:
        print(f"Error captioning image: {e}")
        return ''

# PDF + Table extraction
def extract_pdf(path: str) -> Dict[str, List[str]]:
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
    return {'texts': texts, 'tables': tables}

# Image extraction
def extract_images(path: str, out_dir: str = 'figures') -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    pymupdf4llm.to_markdown(
        path,
        write_images=True,
        image_path=out_dir,
        image_format='png',
        dpi=300,
        page_chunks=True
    )
    return [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith('.png')]

# Main RAG pipeline
def process(path: str):
    existing = next((r for r in records if r['path'] == path), None)
    if existing:
        print('Already processed:', path)
        docs = vectorstore.similarity_search(
            'What is scaled dot product?', k=5,
            filter={ID_KEY: existing['doc_id']}
        )
        for doc in docs:
            print(doc.page_content, '\n' + '-'*40)
        return

    doc_id = str(uuid.uuid4())
    print('Processing', path)
    data = extract_pdf(path)
    imgs = extract_images(path)

    # only image captions now
    img_captions = [caption_image(i) for i in imgs] if imgs else []

    # upsert raw text, tables, and image captions
    def upsert_list(contents, originals, kind):
        ids = [str(uuid.uuid4()) for _ in contents]
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