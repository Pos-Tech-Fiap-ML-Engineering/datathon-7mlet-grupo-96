"""Local RAG knowledge base for the LLM assistant.

Uses `InMemoryVectorStore` instead of a persisted vector DB (e.g. Chroma):
the corpus is a handful of short markdown files, rebuilt from source on every
process start, so a persisted external store would add dependency weight
without a real benefit at this scale.

Indexes `reports/` alongside the policy docs so the assistant can answer
"resuma experimentos": the written technical reports (comparação de
algoritmos, avaliação offline, geração de dados) already hold the experiment
results in prose. A live MLflow tracking server is a later-stage (MLOps)
concern and isn't required for this capability today.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_SOURCE_DIRS = ["data/synthetic_enrichment/policy_docs", "reports"]


def load_knowledge_documents(source_dirs: list[str | Path]) -> list[Document]:
    documents = []
    for source_dir in source_dirs:
        source_dir = Path(source_dir)
        for path in sorted(source_dir.glob("*.md")):
            documents.append(
                Document(page_content=path.read_text(), metadata={"source": str(path)})
            )
    return documents


def build_knowledge_base(
    source_dirs: list[str | Path] | None = None,
    embeddings: Embeddings | None = None,
) -> InMemoryVectorStore:
    source_dirs = source_dirs if source_dirs is not None else DEFAULT_SOURCE_DIRS
    documents = load_knowledge_documents(source_dirs)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(documents)

    if embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_documents(chunks)
    return vector_store
