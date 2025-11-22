# setup_index_enhanced.py
import os
from pathlib import Path

def setup():
    print("🚀 Iniciando setup do sistema SAP Bot (Versão Inteligente)...")
    
    # Verifica dependências
    try:
        from document_preprocessor import DocumentPreprocessor
        from embedding_manager_enhanced import EnhancedEmbeddingManager
        print("✅ Dependências carregadas")
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return
    
    # Verifica arquivo de documentação
    doc_path = 'data/sap_document_text.txt'
    if not os.path.exists(doc_path):
        print(f"❌ Arquivo não encontrado: {doc_path}")
        return
    
    try:
        # Processa documentação com chunks menores
        print("📄 Processando documentação em chunks inteligentes...")
        preprocessor = DocumentPreprocessor(chunk_size=400, overlap=50)
        chunks_df = preprocessor.process_document(doc_path)
        print(f"✅ {len(chunks_df)} chunks criados")
        
        # Mostra estatísticas
        avg_chars = chunks_df['char_count'].mean()
        avg_words = chunks_df['word_count'].mean()
        print(f"📊 Média: {avg_chars:.0f} caracteres, {avg_words:.0f} palavras por chunk")
        
        # Gera embeddings
        print("🔮 Gerando embeddings inteligentes...")
        emb_manager = EnhancedEmbeddingManager("all-MiniLM-L6-v2")
        emb_manager.create_index(chunks_df)
        
        # Salva índice
        print("💾 Salvando índice...")
        emb_manager.save('index_data')
        
        print("\n🎉 SETUP INTELIGENTE COMPLETO!")
        print("👉 Agora execute: streamlit run app_enhanced.py")
        
    except Exception as e:
        print(f"❌ Erro durante o setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup()