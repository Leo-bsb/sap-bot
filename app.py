# app_enhanced_final_simplified.py
"""
Versão melhorada com:
- Design moderno e profissional
- Histórico de conversas (sem persistência)
- Exemplos clicáveis funcionais
- Métricas e estatísticas
- UI responsiva e intuitiva
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
        "chat_history": [],  # Lista de conversas anteriores
        "current_chat_id": 0,
        "emb_manager": None,
        "system_ready": False,
        "total_queries": 0,
        "last_error": None,
        "_load_attempted": False,
        "pending_question": None,  # Para processar perguntas dos exemplos
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

    parts.append(f"**{intent_titles.get(sr.intent, 'Resultados encontrados:')}**\n")

    if sr.recommended_functions:
        parts.append("**Funções sugeridas:** `" + "`, `".join(sr.recommended_functions) + "`\n")

    for i, r in enumerate(sr.results[:5], 1):
        sim = r.get("similarity")
        try:
            sim_text = f"*(relevância: {sim:.1%})*" if isinstance(sim, (float, int)) else ""
        except:
            sim_text = ""

        text = r.get("text") or r.get("snippet") or "[sem texto]"
        parts.append(f"**{i}.** {text} {sim_text}\n")

    parts.append("\n---")
    parts.append("💡 *Para detalhes completos, consulte a documentação oficial do SAP Data Services.*")

    return "\n".join(parts)


# --- Nova conversa ---
def new_chat():
    if st.session_state.messages:
        # Salvar conversa atual no histórico
        st.session_state.chat_history.append({
            "id": st.session_state.current_chat_id,
            "messages": st.session_state.messages.copy(),
            "created_at": datetime.now(),
            "title": st.session_state.messages[0]["content"][:50] + "..." if st.session_state.messages else "Conversa vazia"
        })
    
    st.session_state.messages = []
    st.session_state.current_chat_id += 1
    st.session_state.total_queries = 0


# --- Carregar conversa do histórico ---
def load_chat(chat_id):
    for chat in st.session_state.chat_history:
        if chat["id"] == chat_id:
            st.session_state.messages = chat["messages"].copy()
            st.session_state.current_chat_id = chat_id
            break


# --- Processar pergunta ---
def process_question(question: str):
    if not st.session_state.system_ready:
        st.error("⚠️ O sistema ainda não foi carregado. Aguarde...")
        return

    # Adicionar pergunta do usuário
    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "ts": datetime.utcnow().isoformat()
    })
    st.session_state.total_queries += 1

    # Processar resposta
    try:
        emb = st.session_state.emb_manager
        raw = emb.search_intelligent(question, k=5)

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

        response = render_response(question, sr)
        
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


# --- Sidebar melhorada ---
def sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/0066CC/FFFFFF?text=SAP+DS", use_container_width=True)
        
        st.markdown("### 🎯 Controles Rápidos")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Nova Conversa", use_container_width=True):
                new_chat()
        with col2:
            if st.button("🗑️ Limpar Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.total_queries = 0

        st.markdown("---")

        # Status do sistema
        st.markdown("### 📊 Status do Sistema")
        if st.session_state.system_ready:
            st.success("✅ Sistema Operacional")
        else:
            st.warning("⏳ Carregando...")
        
        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Perguntas", st.session_state.total_queries)
        with col2:
            st.metric("Conversas", len(st.session_state.chat_history))

        st.markdown("---")

        # Exemplos de perguntas
        st.markdown("### 💡 Perguntas de Exemplo")
        st.caption("Clique para testar:")
        
        examples = [
            ("🔍 Como usar a função decode?", "decode"),
            ("✅ Como fazer validação de dados?", "validation"),
            ("📅 Como trabalhar com datas?", "dates"),
            ("🔤 Como manipular strings?", "strings"),
            ("📊 Como fazer agregações?", "aggregation"),
        ]
        
        for label, key in examples:
            if st.button(label, key=f"example_{key}", use_container_width=True):
                question = label.split(" ", 1)[1]  # Remove o emoji
                st.session_state.pending_question = question

        st.markdown("---")

        # Histórico de conversas
        if st.session_state.chat_history:
            st.markdown("### 📚 Histórico de Conversas")
            st.caption(f"{len(st.session_state.chat_history)} conversa(s) anterior(es)")
            
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Últimas 5
                with st.expander(f"💬 {chat['title']}", expanded=False):
                    st.caption(f"🕐 {chat['created_at'].strftime('%d/%m %H:%M')}")
                    if st.button("📂 Carregar", key=f"load_chat_{chat['id']}", use_container_width=True):
                        load_chat(chat["id"])
                        st.rerun()

        # Rodapé
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            <p>🤖 SAP Data Services AI Assistant</p>
            <p>Powered by Advanced RAG</p>
        </div>
        """, unsafe_allow_html=True)


# --- Main ---
def main():
    st.set_page_config(
        page_title="SAP DS AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS customizado
    st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .stChatMessage {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stButton > button {
            border-radius: 5px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem;
            font-weight: bold;
            color: #0066CC;
        }
    </style>
    """, unsafe_allow_html=True)
    
    init_state()

    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🤖 SAP Data Services AI Assistant")
        st.markdown("*Seu assistente inteligente para documentação SAP DS*")

    sidebar()

    # Lazy load do índice
    if not st.session_state.system_ready and not st.session_state._load_attempted:
        st.session_state._load_attempted = True
        with st.spinner("🚀 Inicializando sistema inteligente..."):
            emb = load_embedding_manager()
            if emb:
                st.session_state.emb_manager = emb
                st.session_state.system_ready = True
                st.success("✅ Sistema carregado com sucesso!")
            else:
                st.error(f"❌ Erro: {st.session_state.last_error}")

    st.markdown("---")

    # Container do chat
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            # Tela de boas-vindas
            st.markdown("""
            <div style='text-align: center; padding: 50px;'>
                <h2>👋 Bem-vindo ao SAP DS Assistant!</h2>
                <p style='font-size: 1.2em; color: #666;'>
                    Faça perguntas sobre SAP Data Services e obtenha respostas precisas
                    baseadas na documentação oficial.
                </p>
                <p style='color: #999;'>
                    💡 Experimente os exemplos na barra lateral ou digite sua pergunta abaixo.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render histórico de mensagens
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # Processar pergunta pendente dos exemplos
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        process_question(question)
        st.rerun()

    # Input do usuário
    user_input = st.chat_input("💬 Digite sua pergunta sobre SAP Data Services...")
    
    if user_input and user_input.strip():
        process_question(user_input)
        st.rerun()


if __name__ == "__main__":
    main()
