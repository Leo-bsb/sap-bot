# app_enhanced.py
import streamlit as st
import os
from pathlib import Path
import sys
from typing import List, Dict
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.write("🔑 GEMINI_API_KEY está definida?", bool(os.getenv("GEMINI_API_KEY")))


def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'emb_manager' not in st.session_state:
        st.session_state.emb_manager = None
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0

def get_intelligent_response(user_query: str, search_result: Dict) -> str:
    """Gera resposta inteligente - prioriza resposta natural do Gemini"""
    
    # Se temos resposta natural do Gemini, usa ela
    if search_result.get('natural_response'):
        return search_result['natural_response']
    
    # Fallback para resposta baseada em templates
    intent = search_result['intent']
    recommended_functions = search_result['recommended_functions']
    results = search_result['results']
    
    # Respostas baseadas na intenção (fallback)
    intent_responses = {
        'conditional_logic': "**Para lógica condicional**, recomendo estas funções:",
        'data_lookup': "**Para consultas em tabelas**, estas funções são úteis:",
        'data_validation': "**Para validação de dados**, use:",
        'string_operations': "**Para manipulação de texto**, recomendo:",
        'date_operations': "**Para operações com datas**, consulte:",
        'aggregation': "**Para agregação de dados**, estas funções ajudam:",
        'general_search': "**Baseado na sua pergunta**:"
    }
    
    response = ""
    
    if results:
        response += f"{intent_responses.get(intent, 'Encontrei estas informações:')}\n\n"
        
        if recommended_functions:
            response += f"**Funções recomendadas:** {', '.join(recommended_functions)}\n\n"
        
        for i, result in enumerate(results[:3], 1):
            response += f"**{i}. 📄** (Similaridade: {result['similarity']:.3f})\n"
            response += f"{result['text']}\n\n"
            
        response += "---\n"
        response += "💡 **Dica:** Para mais detalhes, consulte a documentação completa do SAP Data Services."
    else:
        response = "Não encontrei informações específicas na documentação. Tente reformular sua pergunta."
    
    return response

def render_header():
    """Renderiza cabeçalho profissional"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div style='padding: 1.5rem 0;'>
            <h1 style='margin: 0; color: #0066CC;'>
                🤖 SAP Data Services AI Assistant
            </h1>
            <p style='margin: 0.5rem 0 0 0; color: #666; font-size: 1.1rem;'>
                Assistente inteligente com RAG + Gemini 2.5 Flash
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: right; padding-top: 1rem;'>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 0.5rem 1rem; border-radius: 8px; color: white;
                        font-weight: bold; font-size: 0.9rem;'>
                ⚡ Powered by Gemini
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_project_info():
    """Renderiza informações do projeto para recrutadores"""
    with st.expander("📋 Sobre este Projeto", expanded=False):
        st.markdown("""
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
        
        ### 🔬 Arquitetura
        ```
        Consulta do Usuário
              ↓
        Análise de Intenção
              ↓
        Busca Vetorial (RAG)
              ↓
        Gemini 2.5 Flash (Geração)
              ↓
        Resposta Natural em PT-BR
        ```
        
        ---
        💼 **Desenvolvido como solução para o problema real:** IAs gerais não conhecem especificidades 
        do SAP Data Services ECC, gerando respostas genéricas e imprecisas.
        """)

def render_sidebar():
    """Renderiza sidebar com informações e controles"""
    with st.sidebar:
        st.markdown("### ⚙️ Painel de Controle")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recarregar", use_container_width=True):
                st.session_state.emb_manager = None
                st.session_state.system_ready = False
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        st.markdown("---")
        
        # Status do Sistema
        st.markdown("### 📊 Status do Sistema")
        
        if st.session_state.system_ready:
            total_chunks = st.session_state.emb_manager.chunks_df.shape[0]
            
            # Métricas visuais
            st.metric(
                label="📚 Chunks Indexados",
                value=f"{total_chunks:,}",
                delta="Sistema pronto"
            )
            
            st.metric(
                label="💬 Consultas Realizadas",
                value=st.session_state.total_queries
            )
            
            # Status do Gemini
            gemini_status = "❌ Não disponível"
            if hasattr(st.session_state.emb_manager, 'gemini_assistant'):
                if st.session_state.emb_manager.gemini_assistant:
                    gemini_status = "✅ Ativo"
                    st.success("🤖 Gemini conectado")
                else:
                    gemini_status = "⚠️ Offline"
                    st.warning("⚠️ Modo fallback ativo")
        else:
            st.error("❌ Sistema não inicializado")
        
        st.markdown("---")
        
        # Exemplos de perguntas
        st.markdown("### 💡 Perguntas Exemplo")
        exemplos = [
            "Como usar a função LOOKUP?",
            "Como fazer validação de dados?",
            "Diferença entre MERGE e INSERT?",
            "Como trabalhar com datas?",
            "Qual a sintaxe do CASE WHEN?"
        ]
        
        for exemplo in exemplos:
            if st.button(f"💭 {exemplo}", key=exemplo, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": exemplo})
                st.rerun()
        
        st.markdown("---")
        
        # Rodapé
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: #888; font-size: 0.85rem;'>
            <p><b>SAP DS AI Assistant</b></p>
            <p>Desenvolvido com ❤️ usando<br/>Streamlit + Gemini</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Configuração da página
    st.set_page_config(
        page_title="SAP Data Services AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS customizado
    st.markdown("""
    <style>
        /* Estilo geral */
        .stApp {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* Chat messages */
        .stChatMessage {
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Botões */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: 600;
            font-size: 1rem;
        }
        
        /* Métricas */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
            font-weight: bold;
        }

        
        /* Input de chat */
        .stChatInputContainer {
            border-top: 2px solid #e0e0e0;
            padding-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    # Renderizar componentes
    render_header()
    render_project_info()
    
    # Sidebar
    render_sidebar()
    
    # Inicializar sistema
    if not st.session_state.system_ready:
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.spinner("🚀 Inicializando sistema inteligente..."):
                try:
                    from embedding_manager_enhanced import EnhancedEmbeddingManager
                    
                    emb_manager = EnhancedEmbeddingManager()
                    
                    if Path('index_data').exists():
                        emb_manager.load('index_data')
                        st.session_state.emb_manager = emb_manager
                        st.session_state.system_ready = True
                        
                        # Status de inicialização
                        gemini_status = "com Gemini" if emb_manager.gemini_assistant else "em modo fallback"
                        st.success(f"✅ Sistema carregado {gemini_status}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("""
                        ❌ **Índice não encontrado!**
                        
                        Execute primeiro:
                        ```bash
                        python setup_index.py
                        ```
                        """)
                        st.stop()
                except Exception as e:
                    st.error(f"❌ Erro ao inicializar: {e}")
                    st.stop()
    
    # Área de chat
    st.markdown("---")
    
    # Mostrar histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input do usuário
    if prompt := st.chat_input("💬 Digite sua pergunta sobre SAP Data Services..."):
        if not st.session_state.system_ready:
            st.error("⚠️ Sistema não carregado!")
            return
        
        # Incrementar contador
        st.session_state.total_queries += 1
        
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Gerar resposta
        with st.chat_message("assistant"):
            with st.spinner("🔍 Analisando documentação e gerando resposta..."):
                try:
                    # Busca inteligente
                    search_result = st.session_state.emb_manager.search_intelligent(prompt, k=5)
                    
                    # Gera resposta
                    response = get_intelligent_response(prompt, search_result)
                    
                    st.markdown(response)
                    
                    # Mostrar detalhes técnicos em expander
                    with st.expander("🔍 Detalhes Técnicos da Busca"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**📊 Análise:**")
                            st.write(f"• Intenção detectada: `{search_result['intent']}`")
                            st.write(f"• Resultados encontrados: `{len(search_result['results'])}`")
                            st.write(f"• Gemini utilizado: `{'Sim' if search_result.get('gemini_used') else 'Não'}`")
                        
                        with col2:
                            if search_result['recommended_functions']:
                                st.write("**🎯 Funções Recomendadas:**")
                                for func in search_result['recommended_functions']:
                                    st.write(f"• `{func}`")
                        
                        if search_result['results']:
                            st.write("**📈 Scores de Similaridade:**")
                            for i, r in enumerate(search_result['results'][:5], 1):
                                similarity_pct = r['similarity'] * 100
                                st.progress(r['similarity'], text=f"{i}. Chunk {r['chunk_id']}: {similarity_pct:.1f}%")
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
                        
                except Exception as e:
                    error_msg = f"❌ **Erro ao processar pergunta:**\n\n`{str(e)}`\n\nTente reformular ou entre em contato com o suporte."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

if __name__ == "__main__":
    main()
