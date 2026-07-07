from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from bandit_platform.assistant.explain import explain_decision
from bandit_platform.assistant.knowledge_base import build_knowledge_base
from bandit_platform.assistant.llm import get_chat_model
from bandit_platform.assistant.qa import answer_question
from bandit_platform.policies.features import JOB_CATEGORIES
from bandit_platform.service.active_policy import get_active_policy
from bandit_platform.service.core import decide

AUDIT_LOG_PATH = Path("logs/decisions.jsonl")
POUTCOME_OPTIONS = ["failure", "nonexistent", "success"]
DEFAULT_OPTIONS = ["no", "yes", "unknown"]


@st.cache_resource
def _cached_policy():
    return get_active_policy()


@st.cache_resource
def _cached_knowledge_base():
    return build_knowledge_base()


@st.cache_resource
def _cached_llm():
    return get_chat_model()


def render_decision_tab() -> None:
    st.header("Decisao")
    with st.form("decision_form"):
        job = st.selectbox("Ocupacao (job)", JOB_CATEGORIES)
        age = st.number_input("Idade", min_value=18, max_value=110, value=35)
        poutcome = st.selectbox("Resultado da campanha anterior (poutcome)", POUTCOME_OPTIONS)
        default = st.selectbox("Credito em default", DEFAULT_OPTIONS)
        previous = st.number_input("Contatos anteriores (previous)", min_value=0, value=0)
        submitted = st.form_submit_button("Obter decisao")

    if submitted:
        context = {
            "job": job,
            "age": int(age),
            "poutcome": poutcome,
            "default": default,
            "previous": int(previous),
        }
        policy, policy_version = _cached_policy()
        result = decide(context, policy, policy_version, AUDIT_LOG_PATH)

        st.success(f"Braco escolhido: **{result.arm_id}**")
        st.write(f"Reason code: `{result.reason_code}`")
        st.write(f"Versao da politica: `{result.policy_version}`")
        st.write(f"Decision ID: `{result.decision_id}`")
        st.caption(f"Registrado em {result.timestamp} — ver {AUDIT_LOG_PATH}")


def render_assistant_tab() -> None:
    st.header("Assistente")
    st.caption(
        "Pergunte sobre as politicas comerciais sinteticas ou os relatorios de "
        "experimentos, ou explique uma decisao passada pelo decision_id."
    )

    mode = st.radio("O que voce quer fazer?", ["Fazer uma pergunta", "Explicar uma decisao"])

    if mode == "Fazer uma pergunta":
        question = st.text_input("Sua pergunta")
        if st.button("Perguntar") and question:
            vector_store = _cached_knowledge_base()
            llm = _cached_llm()
            result = answer_question(question, vector_store, llm)
            st.write(result["answer"])
            if result["sources"]:
                st.caption("Fontes: " + ", ".join(result["sources"]))
    else:
        decision_id = st.text_input("Decision ID")
        if st.button("Explicar") and decision_id:
            llm = _cached_llm()
            result = explain_decision(decision_id, AUDIT_LOG_PATH, llm)
            if not result["found"]:
                st.error(f"Nenhuma decisao encontrada com decision_id={decision_id}")
            else:
                st.write(result["explanation"])
                st.json(result["record"])


def render_audit_log_tab() -> None:
    st.header("Log de auditoria")
    if not AUDIT_LOG_PATH.exists():
        st.info("Nenhuma decisao registrada ainda nesta maquina.")
        return

    entries = []
    with AUDIT_LOG_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    st.write(f"{len(entries)} decisao(oes) registrada(s).")
    st.dataframe(entries)


def main() -> None:
    st.set_page_config(page_title="Bandit Platform - Datathon 7MLET", layout="wide")
    st.title("Plataforma de Experimentacao Adaptativa")

    tab_decision, tab_assistant, tab_audit = st.tabs(["Decisao", "Assistente", "Log de Auditoria"])
    with tab_decision:
        render_decision_tab()
    with tab_assistant:
        render_assistant_tab()
    with tab_audit:
        render_audit_log_tab()


main()
