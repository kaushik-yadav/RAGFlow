import json
import os
import time
import uuid

from langchain.schema import Document

from rag.captioning import caption_image
from rag.extractors import extract_images, extract_pdf
from rag.rag_constants import ID_KEY, MAX_DOCS, PROCESSED_FILE
from rag.retriever_setup import docstore, vectorstore

if os.path.exists(PROCESSED_FILE):
    records = json.load(open(PROCESSED_FILE))
else:
    records = []

# add the documents in the vector store
def upsert_list(contents, originals, kind, doc_id):
    # get all the ids, if image then store with citations othewise for text store directly
    ids = [str(uuid.uuid4()) for _ in contents]
    if kind == 'image':
        docs = [Document(
            page_content=item['content'],
            metadata={ID_KEY: doc_id, 'type': kind, 'page': item['original']['page'], 'figure': item['original']['figure'], 'filename': item['original']['filename']}
        ) for item in contents]
    else:
        docs = [Document(page_content=content, metadata={ID_KEY: doc_id, 'type': kind}) for content in contents]
    vectorstore.add_documents(docs)
    docstore.mset(list(zip(ids, originals)))

# the main RAG pipeline to extraction , summarize and store content
def process(path):
    doc_id = str(uuid.uuid4())
    print('Processing', path)
    data = extract_pdf(path)
    imgs = extract_images(path)

    img_captions = []
    for i in imgs:
        cap = caption_image(i['path'])
        if cap:
            img_captions.append({
                'content': f"[Figure {i['figure']}, Page {i['page']}]: {cap}",
                'original': i
            })

    if data['texts']:
        upsert_list(data['texts'], data['texts'], 'text', doc_id)
    if data['tables']:
        upsert_list(data['tables'], data['tables'], 'table', doc_id)
    if img_captions:
        upsert_list(img_captions, imgs, 'image', doc_id)

    records.append({'path': path, 'doc_id': doc_id, 'timestamp': time.time()})
    if len(records) > MAX_DOCS:
        oldest = min(records, key=lambda r: r['timestamp'])
        vectorstore.delete(filter={ID_KEY: oldest['doc_id']})
        records.remove(oldest)
    json.dump(records, open(PROCESSED_FILE, 'w'), indent=2)
    print('Completed:', path)
