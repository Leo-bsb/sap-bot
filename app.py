# app_enhanced_fixed_final.py
"""
Versão final corrigida do app Streamlit — pronta para deploy.
Principais mudanças:
- Reset seguro via flag (_reset_app) — não limpa session_state durante renderização.
- Lazy-load seguro do EnhancedEmbeddingManager.
- Evita chamadas problemáticas de st.experimental_rerun() dentro da sidebar.
- Tratamento robusto de erros e logs mínimos no UI.
- Uso da dataclass SearchResult para normalizar saída do emb_manager.
"""

import streamlit as st
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

# garantir import local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Dataclass para padronizar resultados ---
@dataclass
class SearchResult:
    intent: str = ""
    recommended_functions: List[str] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    natural_response: Optional[str] = None
    gemini_used: bool = False


# --- Inicialização do session state ---
def init_session_state():
    defaults = {
        "messages": [],               # histórico do chat
        "emb_manager": None,          # EnhancedEmbeddingManager instanciado
        "system_ready": False,        # sistema inicializado?
        "total_queries": 0,           # contador de queries
        "last_error": None,           # último erro ocorrido
        "_reset_app": False,          # flag para reset seguro
        "_load_attempted": False      # se já tentamos carregar o emb_manager
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# --- Função para gerar resposta a partir do SearchResult ---
def get_intelligent_response(user_query: str, search_result: SearchResult) -> str:
    if search_result is None:
        return "❌ Erro: Resultado de busca inválido. Tente novamente ou verifique o índice."

    if search_result.natural_response:
        return search_result.natural_response

    intent = search_result.intent or "general_search"
    recommended_functions = search_result.recommended_functions or []
    results = search_result.results or []

    intent_responses = {
        "conditional_logic": "**Para lógica condicional**, recomendo estas funções:",
        "data_lookup": "**Para consultas em tabelas**, estas funções são úteis:",
        "data_validation": "**Para validação de dados**, use:",
        "string_operations": "**Para manipulação de texto**, recomendo:",
        "date_operations": "**Para operações com datas**, consulte:",
        "aggregation": "**Para agregação de dados**, estas funções ajudam:",
        "general_search": "**Baseado na sua pergunta**:"
    }

    if not results:
        return "Não encontrei informações específicas na documentação. Tente reformular sua pergunta."

    lines = [intent_responses.get(intent, "Encontrei estas informações:")]

    if recommended_functions:
        lines.append(f"**Funções recomendadas:** {', '.join(recommended_functions)}")

    for i, r in enumerate(results[:5], 1):
        sim = r.get("similarity")
        try:
            sim_txt = f"(Similaridade: {sim:.3f})" if isinstance(sim, (float, int)) else ""
        except Exception:
            sim_txt = ""
        text = r.get("text") or r.get("snippet") or "[sem texto]"
        lines.append(f"**{i}. 📄** {sim_txt} {text}")

    lines.append("---")
    lines.append("💡 **Dica:** Para mais detalhes, consulte a documentação completa do SAP Data Services.")
    return "\n".join(lines)


# --- Render UI: header / project info / sidebar ---
def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            """
            <div style='padding: 1.5rem 0;'>
                <h1 style='margin: 0; color: #0066CC;'>🤖 SAP Data Services AI Assistant</h1>
                <p style='margin: 0.5rem 0 0 0; color: #666; font-size: 1.1rem;'>
                    Assistente inteligente com RAG + Gemini
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div style='text-align: right; padding-top: 1rem;'>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 0.5rem 1rem; border-radius: 8px; color: white;
                            font-weight: bold; font-size: 0.9rem;'>
                    ⚡ Powered by Gemini
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_project_info():
    with st.expander("📋 Sobre este Projeto", expanded=False):
        st.markdown(
            """
            ### 🎯 Objetivo
            Assistente de IA especializado em **SAP Data Services ECC**, utilizando técnicas modernas de RAG 
            (Retrieval-Augmented Generation) para fornecer respostas precisas baseadas na documentação oficial.

            ### 🛠️ Tecnologias Utilizadas
            - **🤖 LLM:** Google Gemini
            - **🔍 RAG:** Embeddings vetoriais + Busca semântica
            - **💾 Base de Conhecimento:** Documentação oficial SAP Data Services
            - **🎨 Interface:** Streamlit
            """
        )


def render_sidebar():
    # Observação: a sidebar DEVE apenas desenhar interface e setar flags mínimas.
    with st.sidebar:
        st.markdown("### ⚙️ Painel de Controle")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recarregar"):
                # sinalizamos reset; o main() fará o reset com segurança
                st.session_state._reset_app = True
                st.experimental_rerun()  # agora é seguro porque estamos apenas marcando flag e retornando

        with col2:
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages = []
                st.session_state.total_queries = 0

        st.markdown("---")

        st.markdown("### 📊 Status do Sistema")
        if st.session_state.system_ready and st.session_state.emb_manager is not None:
            emb = st.session_state.emb_manager
            total_chunks = None
            try:
                if hasattr(emb, "chunks_df") and getattr(emb, "chunks_df") is not None:
                    # polars DataFrame shape -> (n_rows, n_cols)
                    total_chunks = getattr(emb, "chunks_df").shape[0]
            except Exception:
                total_chunks = None

            st.metric(label="📚 Chunks Indexados", value=f"{total_chunks:,}" if total_chunks is not None else "—")
            st.metric(label="💬 Consultas Realizadas", value=st.session_state.total_queries)

            if hasattr(emb, "gemini_assistant") and emb.gemini_assistant:
                st.success("🤖 Gemini conectado")
            else:
                st.warning("⚠️ Gemini não conectado - modo fallback")
        else:
            st.error("❌ Sistema não inicializado")

        st.markdown("---")
        st.markdown("### 💡 Perguntas Exemplo")
        exemplos = [
            "Como usar a função LOOKUP?",
            "Como fazer validação de dados?",
            "Diferença entre MERGE e INSERT?",
            "Como trabalhar com datas?",
            "Qual a sintaxe do CASE WHEN?"
        ]
        for exemplo in exemplos:
            if st.button(f"💭 {exemplo}", key=f"ex_{exemplo}"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": exemplo,
                    "ts": datetime.utcnow().isoformat()
                })

        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; padding: 1rem 0; color: #888; font-size: 0.85rem;'>
                <p><b>SAP DS AI Assistant</b></p>
                <p>Desenvolvido com ❤️ usando<br/>Streamlit + Gemini</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- Safe loader para o EnhancedEmbeddingManager ---
def safe_load_embedding_manager(path: str = "index_data") -> Optional[object]:
    """
    Tenta criar e carregar o EnhancedEmbeddingManager.
    Em caso de erro: grava em session_state.last_error e retorna None.
    """
    try:
        from embedding_manager_enhanced import EnhancedEmbeddingManager
    except Exception as e:
        st.session_state.last_error = f"ImportError EnhancedEmbeddingManager: {e}"
        return None

    try:
        emb_manager = EnhancedEmbeddingManager()
        if Path(path).exists():
            emb_manager.load(path)
        else:
            st.session_state.last_error = f"Índice não encontrado em: {path}"
            return None
        return emb_manager
    except Exception as e:
        st.session_state.last_error = f"Erro ao instanciar/carregar o emb_manager: {e}"
        return None


# --- Main app ---
def main():
    st.set_page_config(page_title="SAP Data Services AI Assistant", page_icon="🤖", layout="wide")

    # custom CSS leve
    st.markdown(
        """
        <style>
            .stApp { max-width: 1400px; margin: 0 auto; }
            .stButton > button { border-radius: 8px; font-weight: 500; transition: all 0.3s ease; }
            .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
            [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_session_state()

    # Reset seguro: só executa no topo do main (fora da renderização da sidebar)
    if st.session_state.get("_reset_app", False):
        # preserva apenas a flag e limpa o resto
        preserve = {"_reset_app": False}
        keys = list(st.session_state.keys())
        for k in keys:
            if k not in preserve:
                del st.session_state[k]
        # re-inicializa defaults e forçar rerun seguro
        init_session_state()
        st.session_state._reset_app = False
        st.experimental_rerun()

    render_header()
    render_project_info()
    render_sidebar()

    # Tentar carregar o emb_manager apenas uma vez por sessão (lazy)
    if not st.session_state.system_ready and not st.session_state._load_attempted:
        st.session_state._load_attempted = True
        with st.spinner("🚀 Inicializando sistema inteligente... (pode demorar alguns segundos)"):
            emb = safe_load_embedding_manager("index_data")
            if emb is not None:
                st.session_state.emb_manager = emb
                st.session_state.system_ready = True
                st.success("✅ Sistema carregado com sucesso!")
            else:
                last = st.session_state.last_error or "Erro desconhecido"
                st.error(f"❌ Não foi possível inicializar o sistema: {last}")
                st.info("Execute `python setup_index.py` localmente se ainda não tiver criado o índice.")

    st.markdown("---")

    # Render histórico de mensagens
    for msg in st.session_state.messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)

    # Input do usuário (retorna apenas quando o usuário submete)
    user_input = st.chat_input("💬 Digite sua pergunta sobre SAP Data Services...")
    if user_input is not None and user_input.strip() != "":
        # Se sistema não está pronto, avisar
        if not st.session_state.system_ready or st.session_state.emb_manager is None:
            st.error("⚠️ Sistema não carregado ou índice ausente. Carregue o índice primeiro.")
        else:
            # registrar user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "ts": datetime.utcnow().isoformat()
            })
            st.session_state.total_queries += 1

            # Processar consulta
            with st.chat_message("assistant"):
                with st.spinner("🔍 Analisando documentação e gerando resposta..."):
                    try:
                        emb = st.session_state.emb_manager
                        raw = emb.search_intelligent(user_input, k=5)

                        # Normalizar raw para SearchResult
                        if raw is None:
                            search_result = SearchResult()
                        elif isinstance(raw, SearchResult):
                            search_result = raw
                        elif isinstance(raw, dict):
                            search_result = SearchResult(
                                intent=raw.get("intent", ""),
                                recommended_functions=raw.get("recommended_functions") or [],
                                results=raw.get("results") or [],
                                natural_response=raw.get("natural_response"),
                                gemini_used=bool(raw.get("gemini_used"))
                            )
                        else:
                            search_result = SearchResult()

                        response_text = get_intelligent_response(user_input, search_result)
                        st.markdown(response_text)

                        # Mostrar detalhes técnicos
                        with st.expander("🔍 Detalhes Técnicos da Busca"):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.write("**📊 Análise:**")
                                st.write(f"• Intenção detectada: `{search_result.intent}`")
                                st.write(f"• Resultados retornados: `{len(search_result.results)}`")
                                st.write(f"• Gemini utilizado: `{'Sim' if search_result.gemini_used else 'Não'}`")
                            with c2:
                                if search_result.recommended_functions:
                                    st.write("**🎯 Funções Recomendadas:**")
                                    for func in search_result.recommended_functions:
                                        st.write(f"• `{func}`")

                            if search_result.results:
                                st.write("**📈 Scores de Similaridade:**")
                                for i, r in enumerate(search_result.results[:5], 1):
                                    sim = r.get("similarity") if isinstance(r, dict) else None
                                    try:
                                        pct = float(sim) if sim is not None else 0.0
                                    except Exception:
                                        pct = 0.0
                                    prog = min(max(pct, 0.0), 1.0)
                                    st.progress(prog, text=f"{i}. Chunk {r.get('chunk_id', '—')}: {pct * 100:.1f}%")

                        # salvar resposta no histórico
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "ts": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        err = f"❌ **Erro ao processar pergunta:** `{e}`"
                        st.error(err)
                        st.session_state.last_error = str(e)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": err,
                            "ts": datetime.utcnow().isoformat()
                        })


if __name__ == "__main__":
    main()
