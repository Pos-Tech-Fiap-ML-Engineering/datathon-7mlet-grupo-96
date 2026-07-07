from langchain_core.embeddings import DeterministicFakeEmbedding

from bandit_platform.assistant.knowledge_base import (
    build_knowledge_base,
    load_knowledge_documents,
)


def _write_markdown(path, name, content):
    (path / name).write_text(content)


def test_load_knowledge_documents_reads_markdown_files(tmp_path):
    _write_markdown(tmp_path, "a.md", "# Politica A\nConteudo da politica A.")
    _write_markdown(tmp_path, "b.md", "# Politica B\nConteudo da politica B.")
    (tmp_path / "ignore.txt").write_text("nao deve ser lido")

    docs = load_knowledge_documents([tmp_path])

    assert len(docs) == 2
    assert {d.metadata["source"] for d in docs} == {
        str(tmp_path / "a.md"),
        str(tmp_path / "b.md"),
    }


def test_load_knowledge_documents_reads_multiple_dirs(tmp_path):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()
    _write_markdown(dir_a, "a.md", "Conteudo A")
    _write_markdown(dir_b, "b.md", "Conteudo B")

    docs = load_knowledge_documents([dir_a, dir_b])

    assert len(docs) == 2


def test_build_knowledge_base_is_searchable(tmp_path):
    _write_markdown(
        tmp_path,
        "cdb.md",
        "Politica de CDB: clientes com credito em default nao sao elegiveis.",
    )
    _write_markdown(
        tmp_path,
        "poupanca.md",
        "Politica de poupanca: sem restricao de idade minima alem da maioridade.",
    )

    vector_store = build_knowledge_base(
        source_dirs=[tmp_path],
        embeddings=DeterministicFakeEmbedding(size=32),
    )
    results = vector_store.similarity_search("qualquer pergunta", k=1)

    assert len(results) == 1
    assert results[0].page_content
