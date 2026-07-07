from types import SimpleNamespace

from langchain_core.embeddings import DeterministicFakeEmbedding

from bandit_platform.assistant.knowledge_base import build_knowledge_base
from bandit_platform.assistant.qa import answer_question


class _FakeLLM:
    def __init__(self, response_text):
        self._response_text = response_text
        self.received_messages = None

    def invoke(self, messages):
        self.received_messages = messages
        return SimpleNamespace(content=self._response_text)


def test_answer_question_returns_answer_and_sources(tmp_path):
    (tmp_path / "policy.md").write_text("Politica: default=yes bloqueia credito.")
    vector_store = build_knowledge_base(
        source_dirs=[tmp_path], embeddings=DeterministicFakeEmbedding(size=32)
    )
    fake_llm = _FakeLLM("Clientes com default=yes nao recebem oferta de credito.")

    result = answer_question("Quem pode receber CDB?", vector_store, fake_llm, k=1)

    assert result["answer"] == "Clientes com default=yes nao recebem oferta de credito."
    assert result["sources"] == [str(tmp_path / "policy.md")]
    assert fake_llm.received_messages is not None


def test_answer_question_includes_retrieved_context_in_prompt(tmp_path):
    (tmp_path / "policy.md").write_text("Frase unica de teste: XYZABC123.")
    vector_store = build_knowledge_base(
        source_dirs=[tmp_path], embeddings=DeterministicFakeEmbedding(size=32)
    )
    fake_llm = _FakeLLM("resposta")

    answer_question("pergunta qualquer", vector_store, fake_llm, k=1)

    system_message = fake_llm.received_messages[0]
    assert "XYZABC123" in system_message.content
