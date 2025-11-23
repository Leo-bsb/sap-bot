# app_enhanced_final_simplified.py
"""
Versão melhorada da interface Streamlit para deploy.
- Exemplos acionam o mesmo fluxo que o input do usuário.
- Histórico em sessão (sem persistência).
- Download do histórico e debug do último SearchResult.
- Carregamento lazy e tratamento de erros.
"""

import streamlit as st
import sys, os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import io

# --- Ajustar path local (se necessário) ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Dataclass para padronizar resultados ---
@dataclass
class SearchResult:
    intent: str = ""
    recommended_functions: List[str] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    natural_response: Optional[str] = None
    gemini_used: bool = False
    raw: Optional[Dict] = None  # para debug


# --- Sessão ---
def init_state():
    defaults = {
        "messages": [],  # lista de dicts {"role": "user"/"assistant", "content": str, "ts": iso, "meta": optional}
        "emb_manager": None,
        "system_ready": False,
        "total_queries": 0,
        "last_error": None,
        "_load_attempted": False,
        "last_search_raw": None,
        "show_timestamps": True,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


# --- Helpers ---
def fmt_ts(iso_ts: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_ts


def render_response_text(user_query: str, sr: SearchResult) -> str:
    """
    Constrói texto final para mostrar ao usuário. Mantive seu formato
    original, com títulos por intent e listagem de resultados.
    """
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

    for i, r in enumerate(sr.results[:7], 1):
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


# --- Processador de queries (unificado para botões e input) ---
def process_user_query(user_query: str):
    """
    Função única que processa queries de usuário — chamada tanto por
    st.chat_input quanto pelos botões de exemplo.
    """
    if not user_query or not user_query.strip():
        return

    # registrar mensagem do usuário
    user_msg = {"role": "user", "content": user_query.strip(), "ts": datetime.utcnow().isoformat()}
    st.session_state.messages.append(user_msg)
    st.session_state.total_queries += 1

    # checar readiness
    if not st.session_state.system_ready:
        err = "❌ O sistema ainda não foi carregado. Tente novamente em alguns instantes."
        st.session_state.last_error = err
        assistant_msg = {"role": "assistant", "content": err, "ts": datetime.utcnow().isoformat()}
        st.session_state.messages.append(assistant_msg)
        return

    # tentar buscar no embedding manager
    try:
        emb = st.session_state.emb_manager
        raw = emb.search_intelligent(user_query, k=5)

        # normalizar SearchResult
        if isinstance(raw, SearchResult):
            sr = raw
            sr.raw = None
        elif isinstance(raw, dict):
            sr = SearchResult(
                intent=raw.get("intent", ""),
                recommended_functions=raw.get("recommended_functions") or [],
                results=raw.get("results") or [],
                natural_response=raw.get("natural_response"),
                gemini_used=bool(raw.get("gemini_used")),
            )
            sr.raw = raw
        else:
            # se o emb retornou algo inesperado, guardamos para debug
            sr = SearchResult()
            sr.raw = {"raw_return": str(raw)}

        # armazenar raw para debug
        st.session_state.last_search_raw = sr.raw

        # montar resposta textual
        response_text = render_response_text(user_query, sr)

        assistant_msg = {
            "role": "assistant",
            "content": response_text,
            "ts": datetime.utcnow().isoformat(),
            "meta": {
                "intent": sr.intent,
                "recommended_functions": sr.recommended_functions,
                "gemini_used": sr.gemini_used,
            },
        }
        st.session_state.messages.append(assistant_msg)

    except Exception as e:
        err = f"❌ Erro ao processar: {e}"
        st.session_state.last_error = str(e)
        assistant_msg = {"role": "assistant", "content": err, "ts": datetime.utcnow().isoformat()}
        st.session_state.messages.append(assistant_msg)


# --- Layout e UI ---
def sidebar_controls():
    with st.sidebar:
        st.header("⚙️ Controles")
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.messages = []
            st.session_state.total_queries = 0

        if st.button("↩️ Desfazer última (apenas mensagem)"):
            if st.session_state.messages:
                st.session_state.messages.pop()

        st.markdown("---")

        st.subheader("📊 Status")
        if st.session_state.system_ready:
            st.success("Sistema carregado")
        else:
            # allow manual retry
            st.warning("Sistema não carregado")
            if st.button("🔁 Tentar carregar novamente"):
                # simply flip flag so main loader attempts again
                st.session_state._load_attempted = False

        st.markdown("---")

        st.subheader("💡 Exemplos (clique para enviar)")
        examples = [
            "Como usar a função LOOKUP?",
            "Como fazer validação de dados?",
            "Como trabalhar com datas?",
        ]
        for ex in examples:
            if st.button(ex):
                process_user_query(ex)

        st.markdown("---")
        st.checkbox("Mostrar timestamps", value=st.session_state.show_timestamps, key="show_timestamps")

        st.markdown("---")
        st.caption("Sem persistência: histórico fica apenas na sessão do Streamlit (memória).")


# --- Render histórico no main area ---
def render_chat_history():
    # área de histórico — scroll natural do Streamlit
    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        ts = fmt_ts(msg.get("ts")) if st.session_state.show_timestamps and msg.get("ts") else None

        # use st.chat_message for consistent UI
        with st.chat_message(role):
            st.markdown(content)
            if ts:
                st.caption(ts)
            # mostrar meta se existir
            if msg.get("meta"):
                with st.expander("► Metadados da resposta", expanded=False):
                    st.json(msg["meta"])


# --- Download do histórico ---
def build_chat_download():
    buf = io.StringIO()
    for msg in st.session_state.messages:
        ts = fmt_ts(msg.get("ts")) if msg.get("ts") else ""
        role = msg.get("role", "")
        content = msg.get("content", "")
        buf.write(f"[{ts}] {role.upper()}:\n{content}\n\n")
    return buf.getvalue().encode("utf-8")


# --- Main ---
def main():
    st.set_page_config(page_title="SAP DS Assistant", page_icon="🤖", layout="wide")
    init_state()

    # Layout: duas colunas (conteúdo e sidebar já existe via st.sidebar)
    st.title("🤖 SAP Data Services AI Assistant")

    sidebar_controls()

    # Lazy load do índice (uma tentativa automática)
    if not st.session_state.system_ready and not st.session_state._load_attempted:
        st.session_state._load_attempted = True
        with st.spinner("Carregando inteligência..."):
            emb = load_embedding_manager()
            if emb:
                st.session_state.emb_manager = emb
                st.session_state.system_ready = True
                st.success("Sistema carregado com sucesso!")
            else:
                st.session_state.system_ready = False
                # last_error já preenchido dentro da função
                st.error(f"Erro: {st.session_state.last_error}")

    st.markdown("---")

    # Top bar actions
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("🔽 Baixar histórico"):
            data = build_chat_download()
            st.download_button("Download .txt", data=data, file_name="chat_history.txt", mime="text/plain")
    with col2:
        if st.session_state.last_search_raw:
            if st.button("🛈 Mostrar último SearchResult (debug)"):
                st.json(st.session_state.last_search_raw)
    with col3:
        st.markdown("Use os exemplos na barra lateral ou digite sua pergunta abaixo.")

    st.markdown("---")

    # Chat renderizado (rodapé com input)
    chat_col, input_col = st.columns([4, 1])
    with chat_col:
        render_chat_history()

    with input_col:
        # Espaço para uma caixa de input simples e um botão — essa opção facilita deploys e execução programática
        st.write("Enviar")
        usr = st.text_area("Pergunta", value="", key="manual_input", height=120)
        if st.button("Enviar pergunta"):
            q = usr.strip()
            if q:
                process_user_query(q)
                # limpar o text_area após envio
                st.session_state.manual_input = ""

    # Alternativamente, fornecer st.chat_input abaixo do histórico (compatível com Streamlit >=1.18)
    # porém deixei o fluxo principal via text_area + botão para garantir envios programáticos
    st.markdown("---")
    st.caption(f"Consultas totais nesta sessão: {st.session_state.total_queries}")

    # Mostrar último erro (se houver)
    if st.session_state.last_error:
        with st.expander("Último erro"):
            st.error(st.session_state.last_error)

    # Footer: aviso sobre não-persistência e debug tips
    st.markdown(
        """
        **Observações:**  
        - Histórico é volátil (fica apenas em memória da sessão).  
        - Se quiser que ao clicar exemplos o texto apareça no campo de input visível, isso exigiria `st.experimental_rerun()` ou hacks que podem quebrar em deploy — optei por processar imediatamente para garantir estabilidade.  
        - Para debug de integrações, veja "Mostrar último SearchResult (debug)".
        """
    )


if __name__ == "__main__":
    main()
