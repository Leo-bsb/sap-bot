# test_environment.py
import torch
import sentence_transformers
import sys

print("🧪 VERIFICAÇÃO DO AMBIENTE")
print("=" * 40)

print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"Sentence Transformers: {sentence_transformers.__version__}")
print(f"CUDA disponível: {torch.cuda.is_available()}")

# Testa carregamento do modelo
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Modelo carregado com sucesso")
    
    # Testa encoding
    embeddings = model.encode(["teste simples"])
    print(f"✅ Embeddings gerados: {embeddings.shape}")
    
except Exception as e:
    print(f"❌ Erro: {e}")

print("=" * 40)