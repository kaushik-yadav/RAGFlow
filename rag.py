import base64
import json
import os
import time
import uuid
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

import pymupdf4llm
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.schema import Document
from langchain.storage import InMemoryStore
from langchain_cohere import CohereEmbeddings
from langchain_community.chat_models import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from PIL import Image
from unstructured.partition.pdf import partition_pdf

CLAUDE_API_KEY   = os.getenv('CLAUDE_API_KEY')
COHERE_API_KEY   = os.getenv('COHERE_API_KEY')
COLLECTION_NAME  = 'multi_modal_rag'
ID_KEY           = 'doc_id'
PROCESSED_FILE   = 'processed.json'
MAX_DOCS         = 5

assert CLAUDE_API_KEY, 'Set CLAUDE_API_KEY in .env'
assert COHERE_API_KEY, 'Set COHERE_API_KEY in .env'

# Load ingestion records
if os.path.exists(PROCESSED_FILE):
    raw = json.load(open(PROCESSED_FILE))
    records = raw if isinstance(raw, list) and all(isinstance(r, dict) for r in raw) else []
else:
    records = []

# Embedding function (Cohere)
embedding_function = CohereEmbeddings(
    model="embed-english-v3.0",
    cohere_api_key=COHERE_API_KEY
)

# Vectorstore setup
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory='./chroma_store',
    embedding_function=embedding_function
)

# Docstore and Retriever
docstore = InMemoryStore()
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    id_key=ID_KEY
)

# Summarization chain using Claude
prompt = ChatPromptTemplate.from_template('Summarize concisely, no extra text:\n{element}')
claude = ChatAnthropic(
    model_name='claude-3.5-100k',
    anthropic_api_key=CLAUDE_API_KEY,
    temperature=0.5
)
summarize_chain = {'element': lambda x: x} | prompt | claude | StrOutputParser()

# Image captioning with Claude Vision (textual placeholder)
def caption_image(path: str) -> str:
    # Embedding image prompt inline; replace with actual multimodal call if supported
    prompt = f"Describe the image at '{path}' in detail under 300 words, no intro."
    return claude.generate([prompt]).generations[0].text

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
    # Check if already ingested
    existing = next((r for r in records if r['path'] == path), None)
    if existing:
        print("Already processed:", path)
        # restrict retrieval to this doc_id
        docs = vectorstore.similarity_search(
            "What is scaled dot product?", k=5,
            filter={ID_KEY: existing['doc_id']}
        )
        for doc in docs:
            print(doc.page_content, "\n" + "-"*40)
        return

    # New ingestion
    doc_id = str(uuid.uuid4())
    print('Processing', path)
    data = extract_pdf(path)
    imgs = extract_images(path)

    # Summarizations
    text_summaries  = summarize_chain.batch(data['texts'],  {'max_concurrency':3}) if data['texts'] else []
    table_summaries = summarize_chain.batch(data['tables'], {'max_concurrency':3}) if data['tables'] else []
    img_summaries   = [caption_image(i) for i in imgs] if imgs else []

    # Upsert into Chroma
    def upsert_list(summaries, originals, kind):
        ids = [str(uuid.uuid4()) for _ in summaries]
        docs_ = [Document(page_content=sm, metadata={ID_KEY: doc_id, 'type': kind})
                 for sm in summaries]
        vectorstore.add_documents(docs_)
        docstore.mset(list(zip(ids, originals)))

    if text_summaries:
        upsert_list(text_summaries, data['texts'], 'text')
    if table_summaries:
        upsert_list(table_summaries, data['tables'], 'table')
    if img_summaries:
        upsert_list(img_summaries, imgs, 'image')
    print("-- Added to ChromaDB")

    # Record ingestion
    records.append({'path': path, 'doc_id': doc_id, 'timestamp': time.time()})

    # Eviction if exceeding MAX_DOCS
    if len(records) > MAX_DOCS:
        oldest = min(records, key=lambda r: r['timestamp'])
        print(f"Evicting oldest: {oldest['path']}")
        vectorstore.delete(filter={ID_KEY: oldest['doc_id']})
        records.remove(oldest)

    # Persist records
    json.dump(records, open(PROCESSED_FILE, 'w'), indent=2)
    print('Done', path)

# main code block
if __name__ == '__main__':
    pdf = "attention.pdf"
    if not os.path.isfile(pdf):
        print('Not found:', pdf)
    else:
        start = time.time()
        process(pdf)
        print('Elapsed', round(time.time() - start, 2), 's')
