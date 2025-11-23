# app_enhanced_final_simplified.py
"""
Versão simplificada, estável e pronta para deploy no Streamlit Cloud.
- Sem experimental_rerun()
- Reset simplificado
- Tratamento de erros robusto
- Lazy load seguro do embedding manager
- Chat limpo e estável
"""

import streamlit as st
import sys, os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

# --- Ajustar path local ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Dataclass para padronizar resultados ---
@dataclass
class SearchResult:
    intent: str = ""
    recommended_functions: List[str] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    natural_response: Optional[str] = None
    gemini_used: bool = False


# --- Sessão ---
def init_state():
    defaults = {
        "messages": [],
        "emb_manager": None,
        "system_ready": False,
        "total_queries": 0,
        "last_error": None,
        "_load_attempted": False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


# --- Carregar o embedding manager ---
def load_embedding_manager(path: str = "index_data"):
    try:
        from embedding_manager_enhanced import EnhancedEmbeddingManager
    except Exception as e:
        st.session_state.last_error = f"Erro ao importar EnhancedEmbeddingManager: {e}"
        return None

    try:
        emb = EnhancedEmbeddingManager()
        if Path(path).exists():
            emb.load(path)
            return emb
        else:
            st.session_state.last_error = f"Índice não encontrado em '{path}'"
            return None
    except Exception as e:
        st.session_state.last_error = f"Erro ao carregar índice: {e}"
        return None


# --- Gerar resposta final ---
def render_response(user_query: str, sr: SearchResult):

    if sr.natural_response:
        return sr.natural_response

    if not sr.results:
        return "Não encontrei informações específicas na documentação."

    parts = []
    intent_titles = {
        "conditional_logic": "🧠 Lógica condicional:",
        "data_lookup": "🔎 Consultas em tabelas:",
        "data_validation": "🔐 Validação de dados:",
        "string_operations": "🔤 Manipulação de texto:",
        "date_operations": "📅 Trabalhar com datas:",
        "aggregation": "📊 Agregações:",
        "general_search": "📘 Baseado na sua pergunta:",
    }

    parts.append(f"**{intent_titles.get(sr.intent, 'Resultados encontrados:')}**")

    if sr.recommended_functions:
        parts.append("**Funções sugeridas:** " + ", ".join(sr.recommended_functions))

    for i, r in enumerate(sr.results[:5], 1):
        sim = r.get("similarity")
        try:
            sim_text = f"(sim: {sim:.3f})" if isinstance(sim, (float, int)) else ""
        except:
            sim_text = ""

        text = r.get("text") or r.get("snippet") or "[sem texto]"
        parts.append(f"**{i}.** {sim_text} {text}")

    parts.append("\n---\n")
    parts.append("💡 *Para detalhes completos, consulte a documentação oficial do SAP Data Services.*")

    return "\n".join(parts)


# --- Layout e UI ---
def sidebar():
    with st.sidebar:
        st.header("⚙️ Controles")

        if st.button("🗑️ Limpar Conversa"):
            st.session_state.messages = []
            st.session_state.total_queries = 0

        st.markdown("---")

        st.subheader("📊 Status")
        if st.session_state.system_ready:
            st.success("Sistema carregado")
        else:
            st.error("Sistema não carregado")

        st.markdown("---")

        st.subheader("💡 Exemplos")
        for ex in [
            "Como usar a função LOOKUP?",
            "Como fazer validação de dados?",
            "Como trabalhar com datas?",
        ]:
            if st.button(ex):
                st.session_state.messages.append({
                    "role": "user",
                    "content": ex,
                    "ts": datetime.utcnow().isoformat()
                })


# --- Main ---
def main():
    st.set_page_config(page_title="SAP DS Assistant", page_icon="🤖", layout="wide")
    init_state()

    st.title("🤖 SAP Data Services AI Assistant")

    sidebar()

    # Lazy load do índice
    if not st.session_state.system_ready and not st.session_state._load_attempted:
        st.session_state._load_attempted = True
        with st.spinner("Carregando inteligência..."):
            emb = load_embedding_manager()
            if emb:
                st.session_state.emb_manager = emb
                st.session_state.system_ready = True
                st.success("Sistema carregado com sucesso!")
            else:
                st.error(f"Erro: {st.session_state.last_error}")

    st.markdown("---")

    # Render histórico
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input do usuário
    user_input = st.chat_input("Digite sua pergunta sobre SAP Data Services...")
    if user_input and user_input.strip():
        if not st.session_state.system_ready:
            st.error("O sistema ainda não foi carregado.")
            return

        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "ts": datetime.utcnow().isoformat()
        })
        st.session_state.total_queries += 1

        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando informação..."):
                try:
                    emb = st.session_state.emb_manager
                    raw = emb.search_intelligent(user_input, k=5)

                    if isinstance(raw, SearchResult):
                        sr = raw
                    elif isinstance(raw, dict):
                        sr = SearchResult(
                            intent=raw.get("intent", ""),
                            recommended_functions=raw.get("recommended_functions") or [],
                            results=raw.get("results") or [],
                            natural_response=raw.get("natural_response"),
                            gemini_used=bool(raw.get("gemini_used")),
                        )
                    else:
                        sr = SearchResult()

                    response = render_response(user_input, sr)
                    st.markdown(response)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "ts": datetime.utcnow().isoformat()
                    })

                except Exception as e:
                    err = f"❌ Erro ao processar: {e}"
                    st.error(err)
                    st.session_state.last_error = str(e)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": err,
                        "ts": datetime.utcnow().isoformat()
                    })


if __name__ == "__main__":
    main()
