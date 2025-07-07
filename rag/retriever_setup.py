from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings

from rag.rag_constants import COHERE_API_KEY, COLLECTION_NAME

# embedding model
embedding_function = CohereEmbeddings(
    model='embed-english-v3.0',
    cohere_api_key=COHERE_API_KEY
)

# vector store config
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory='./chroma_store',
    embedding_function=embedding_function
)

# initiating the memory store
docstore = InMemoryStore()

# RAG retriever
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    id_key='doc_id'
)
