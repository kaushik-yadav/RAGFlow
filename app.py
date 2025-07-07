import os

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

from rag.rag_constants import ID_KEY
from rag.rag_pipeline import process, records
from rag.retriever_setup import vectorstore
from transcribe import transcribe_user_question

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_IMAGE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash-lite-preview-06-17")

# Streamlit page config
st.set_page_config(page_title="Voice-Based RAG", layout="centered")
st.title("🔬 Multimodal Voice-Based RAG Assistant")

# session state for tracking
if "doc_path" not in st.session_state:
    st.session_state.doc_path = None
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None

# uploading the PDF
uploaded = st.file_uploader("📄 Upload a PDF document", type="pdf")
if uploaded is not None:
    with st.spinner("Processing PDF..."):
        path = os.path.join("uploads/", uploaded.name)
        os.makedirs("uploads", exist_ok=True)
        with open(path, "wb") as f:
            f.write(uploaded.read())
        st.session_state.doc_path = path

        # Check if already processed
        existing = next((r for r in records if r['path'] == path), None)
        if existing:
            st.session_state.doc_id = existing["doc_id"]
            st.info("Document already processed.")
        else:
            process(path)
            st.session_state.doc_id = next(
                (r["doc_id"] for r in records if r["path"] == path), None
            )
            st.success("PDF processed successfully!")

# Mic Button
if st.session_state.doc_path:
    st.markdown("### 🎤 Ask a Question via Voice")
    if st.button("🎙️ Record Question"):
        with st.spinner("Transcribing your voice..."):
            question = transcribe_user_question()
            st.markdown("**Transcribed Question:**")
            st.info(question)

        # Perform RAG only if doc_id exists
        if st.session_state.doc_id:
            docs = vectorstore.similarity_search(
                question, k=3,
                filter={ID_KEY: st.session_state.doc_id}
            )
            context = "\n\n".join(d.page_content for d in docs)

            st.markdown("#### 📚 Retrieved Context")
            for i, doc in enumerate(docs):
                st.markdown(f"**Chunk {i+1}**")
                st.info(doc.page_content)

            # Ask Gemini
            st.markdown("#### 🤖 Gemini Answer")
            with st.spinner("Generating answer..."):
                prompt = f"Answer the question using the following context:\n\n{context}\n\nQuestion: {question}"
                response = model.generate_content(prompt)
                st.success(response.text)
        else:
            st.error("Document not processed correctly. Please re-upload.")

# Footer
st.markdown("---")
st.caption("Built with LangChain + Gemini · Streamlit · AssemblyAI STT")
