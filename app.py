# app_enhanced_fixed.py
"""Versão corrigida e mais robusta do app Streamlit fornecido pelo usuário.
Principais melhorias:
- Remove `st.rerun()` na inicialização para evitar loops
- Protege acessos a atributos de emb_manager
- Valida retorno de search_intelligent() antes de usar
- Evita renderização duplicada de mensagens do chat
- Estrutura o resultado da busca em uma dataclass `SearchResult`
- Melhor tratamento de erros e mensagens de fallback
- Comentários e organização para facilitar manutenção
"""

import streamlit as st
import os
from pathlib import Path
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Garantir que o diretório do arquivo atual está no sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class SearchResult:
    intent: str = ""
    recommended_functions: List[str] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    natural_response: Optional[str] = None
    gemini_used: bool = False


def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []  # cada item: {role: 'user'|'assistant', content: str, ts: str}
    if 'emb_manager' not in st.session_state:
        st.session_state.emb_manager = None
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None


def get_intelligent_response(user_query: str, search_result: SearchResult) -> str:
    """Gera resposta priorizando resposta natural quando disponível.
    Recebe um SearchResult (dataclass) para evitar acoplamento a dicts soltos.
    """
    # Checar objeto
    if search_result is None:
        return "❌ Erro: Resultado de busca inválido. Tente novamente ou verifique o índice."

    # Se temos resposta natural do Gemini, usa ela
    if search_result.natural_response:
        return search_result.natural_response

    # Fallback para resposta baseada em templates
    intent = search_result.intent or 'general_search'
    recommended_functions = search_result.recommended_functions or []
    results = search_result.results or []

    intent_responses = {
        'conditional_logic': "**Para lógica condicional**, recomendo estas funções:",
        'data_lookup': "**Para consultas em tabelas**, estas funções são úteis:",
        'data_validation': "**Para validação de dados**, use:",
        'string_operations': "**Para manipulação de texto**, recomendo:",
        'date_operations': "**Para operações com datas**, consulte:",
        'aggregation': "**Para agregação de dados**, estas funções ajudam:",
        'general_search': "**Baseado na sua pergunta**:"
    }

    if not results:
        return "Não encontrei informações específicas na documentação. Tente reformular sua pergunta."

    response_lines = []
    response_lines.append(intent_responses.get(intent, 'Encontrei estas informações:'))

    if recommended_functions:
        response_lines.append(f"**Funções recomendadas:** {', '.join(recommended_functions)}")

    for i, result in enumerate(results[:5], 1):
        similarity = result.get('similarity')
        try:
            sim_txt = f"(Similaridade: {similarity:.3f})" if isinstance(similarity, (float, int)) else ""
        except Exception:
            sim_txt = ""

        text = result.get('text') or result.get('snippet') or "[sem texto]"
        response_lines.append(f"**{i}. 📄** {sim_txt}
{text}
")

    response_lines.append('---')
    response_lines.append('💡 **Dica:** Para mais detalhes, consulte a documentação completa do SAP Data Services.')

    return "

".join(response_lines)


def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            """
        <div style='padding: 1.5rem 0;'>
            <h1 style='margin: 0; color: #0066CC;'>
                🤖 SAP Data Services AI Assistant
            </h1>
            <p style='margin: 0.5rem 0 0 0; color: #666; font-size: 1.1rem;'>
                Assistente inteligente com RAG + Gemini 2.5 Flash
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
        - **🤖 LLM:** Google Gemini 2.5 Flash
        - **🔍 RAG:** Embeddings vetoriais + Busca semântica
        - **💾 Base de Conhecimento:** Documentação oficial SAP Data Services
        - **🎨 Interface:** Streamlit
        - **📊 Análise:** Detecção de intenção + Recomendação contextual

        ### ✨ Diferenciais
        - ✅ Respostas em **português natural** com exemplos práticos
        - ✅ Busca inteligente com **análise de intenção**
        - ✅ **Recomendações contextuais** de funções SAP
        - ✅ Sistema de **fallback robusto** (funciona mesmo sem API)
        - ✅ Interface **responsiva e intuitiva**
        """
        )


def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Painel de Controle")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recarregar Índice"):
                # Em vez de rerun, sinalizamos que o índice precisa ser recarregado
                st.session_state.system_ready = False
                st.session_state.emb_manager = None
                st.session_state.last_error = None
                st.experimental_rerun()

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
                if hasattr(emb, 'chunks_df') and getattr(emb, 'chunks_df') is not None:
                    total_chunks = getattr(emb, 'chunks_df').shape[0]
            except Exception:
                total_chunks = None

            st.metric(label="📚 Chunks Indexados", value=f"{total_chunks:,}" if total_chunks is not None else "—")
            st.metric(label="💬 Consultas Realizadas", value=st.session_state.total_queries)

            gemini_status = "⚠️ Offline"
            if hasattr(emb, 'gemini_assistant') and emb.gemini_assistant:
                gemini_status = "✅ Ativo"
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
            "Qual a sintaxe do CASE WHEN?",
        ]

        for exemplo in exemplos:
            if st.button(f"💭 {exemplo}", key=f"ex_{exemplo}"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": exemplo,
                    "ts": datetime.utcnow().isoformat(),
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


def safe_load_embedding_manager(path: str = 'index_data') -> Optional[object]:
    """Tenta carregar o EnhancedEmbeddingManager, retorna None em falha.
    Mantém os erros logados em session_state.last_error.
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
        st.session_state.last_error = f"Erro ao instanciar/ carregar o emb_manager: {e}"
        return None


def main():
    st.set_page_config(page_title="SAP Data Services AI Assistant", page_icon="🤖", layout="wide")

    # CSS customizado (mantive, mas prefira arquivos separados)
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

    render_header()
    render_project_info()
    render_sidebar()

    # Inicializar sistema (sem usar st.rerun dentro do bloco)
    if not st.session_state.system_ready:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.spinner("🚀 Inicializando sistema inteligente... (isso pode levar alguns segundos)"):
                emb_manager = safe_load_embedding_manager('index_data')
                if emb_manager is not None:
                    st.session_state.emb_manager = emb_manager
                    st.session_state.system_ready = True
                    st.success("✅ Sistema carregado com sucesso!")
                else:
                    # Mostrar erro mais amigável
                    last_err = st.session_state.last_error or "Erro desconhecido"
                    st.error(f"❌ Não foi possível inicializar o sistema: {last_err}")
                    st.info("Execute `python setup_index.py` se ainda não tiver criado o índice.")
                    # Não chamamos st.stop() para permitir inspeção da UI; porém desabilitamos o chat.

    st.markdown("---")

    # Área de chat - renderizar todo o histórico a partir do estado (evita duplicação)
    for message in st.session_state.messages:
        role = message.get('role', 'assistant')
        content = message.get('content', '')
        with st.chat_message(role):
            st.markdown(content)

    # Input do usuário
    prompt = st.chat_input("💬 Digite sua pergunta sobre SAP Data Services...")
    if prompt is not None and prompt.strip() != "":
        if not st.session_state.system_ready or st.session_state.emb_manager is None:
            st.error("⚠️ Sistema não carregado ou índice ausente. Carregue o índice primeiro.")
        else:
            # Incrementar contador
            st.session_state.total_queries += 1

            # Adicionar mensagem do usuário ao histórico; não renderizamos manualmente
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "ts": datetime.utcnow().isoformat(),
            })

            # Gerar resposta e adicionar ao histórico
            with st.chat_message("assistant"):
                with st.spinner("🔍 Analisando documentação e gerando resposta..."):
                    try:
                        emb = st.session_state.emb_manager
                        # Chamar a busca inteligente com proteção
                        raw_result = emb.search_intelligent(prompt, k=5)

                        # Normalizar o resultado em SearchResult
                        if raw_result is None:
                            search_result = SearchResult()
                        elif isinstance(raw_result, SearchResult):
                            search_result = raw_result
                        elif isinstance(raw_result, dict):
                            # Converter dict para dataclass com tolerância a campos ausentes
                            search_result = SearchResult(
                                intent=raw_result.get('intent', ''),
                                recommended_functions=raw_result.get('recommended_functions') or [],
                                results=raw_result.get('results') or [],
                                natural_response=raw_result.get('natural_response'),
                                gemini_used=bool(raw_result.get('gemini_used')),
                            )
                        else:
                            # Tipo inesperado
                            search_result = SearchResult()

                        response = get_intelligent_response(prompt, search_result)

                        st.markdown(response)

                        # Detalhes técnicos (expander)
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
                                    similarity = r.get('similarity') if isinstance(r, dict) else None
                                    try:
                                        pct = float(similarity) if similarity is not None else 0.0
                                    except Exception:
                                        pct = 0.0
                                    # st.progress espera valor entre 0 e 1
                                    try:
                                        prog = min(max(pct, 0.0), 1.0)
                                    except Exception:
                                        prog = 0.0
                                    st.progress(prog, text=f"{i}. Chunk {r.get('chunk_id', '—')}: {pct * 100:.1f}%")

                        # Salvar resposta no histórico
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "ts": datetime.utcnow().isoformat(),
                        })

                    except Exception as e:
                        error_msg = f"❌ **Erro ao processar pergunta:**

`{str(e)}`

Tente reformular ou entre em contato com o suporte."
                        st.error(error_msg)
                        st.session_state.last_error = str(e)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "ts": datetime.utcnow().isoformat(),
                        })


if __name__ == '__main__':
    main()

