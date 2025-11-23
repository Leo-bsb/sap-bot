# embedding_manager_enhanced.py (VERSÃO CORRIGIDA E ESTÁVEL)
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any

import polars as pl
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from intent_classifier import IntentClassifier


# ---------------------------------------------
# Import condicional do Gemini
# ---------------------------------------------
try:
    from gemini_assistant import GeminiAssistant
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Gemini Assistant não disponível")


class EnhancedEmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"🔮 Carregando modelo: {model_name}")

        # 🔥 Correção: não força CPU, evita meta tensors
        self.model = SentenceTransformer(model_name)

        # 🔥 Não alterar dtype global
        # torch.set_default_dtype(torch.float32)  # REMOVIDO

        # Lazy-load do IntentClassifier
        self._intent_classifier = None

        # Inicializa o Gemini (se possível)
        self.gemini_assistant = None
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "sua_chave_aqui":
                try:
                    self.gemini_assistant = GeminiAssistant(api_key)
                    print("✅ Gemini Assistant carregado")
                except Exception as e:
                    print(f"⚠️  Erro ao carregar Gemini: {e}")
            else:
                print("⚠️  API Key do Gemini não configurada")
        else:
            print("⚠️  Gemini não disponível (módulo não encontrado)")

        self.index = None
        self.chunks_df = None

    # ---------------------------------------------
    # IntentClassifier lazy-loaded
    # ---------------------------------------------
    @property
    def intent_classifier(self):
        if self._intent_classifier is None:
            print("🧠 Carregando IntentClassifier...")
            self._intent_classifier = IntentClassifier()
        return self._intent_classifier

    # ---------------------------------------------
    # Criação do índice (FAISS)
    # ---------------------------------------------
    def create_index(self, chunks_df: pl.DataFrame) -> None:
        self.chunks_df = chunks_df
        texts = chunks_df['text'].to_list()

        print(f"🔮 Gerando embeddings para {len(texts)} chunks...")

        embeddings_matrix = self.model.encode(
            texts,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype('float32')

        import faiss  # 🔥 FAISS deve estar no requirements.txt

        dimension = embeddings_matrix.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings_matrix)

        print(f"✅ Índice criado: {len(embeddings_matrix)} embeddings")

    # ---------------------------------------------
    # Busca simples
    # ---------------------------------------------
    def search_single(self, query: str, k: int = 3, min_similarity: float = 0.2) -> List[Dict]:
        import faiss

        if self.index is None:
            raise ValueError("Índice não criado.")

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype('float32')

        k_search = min(k * 2, len(self.chunks_df))
        similarities, indices = self.index.search(query_embedding, k_search)

        results = []
        seen_chunks = set()

        for idx, similarity in zip(indices[0], similarities[0]):
            if (
                idx < len(self.chunks_df)
                and similarity >= min_similarity
                and len(results) < k
            ):
                row = self.chunks_df.row(idx, named=True)
                chunk_id = row['chunk_id']

                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    results.append({
                        'text': row['text'],
                        'chunk_id': chunk_id,
                        'section': row.get('section', 'N/A'),
                        'similarity': float(similarity),
                        'search_term': query
                    })

        return sorted(results, key=lambda x: x['similarity'], reverse=True)

    # ---------------------------------------------
    # Busca inteligente baseada em intenção
    # ---------------------------------------------
    def search_intelligent(self, user_query: str, k: int = 5) -> Dict:
        intent, recommended_functions = self.intent_classifier.classify_intent(user_query)
        search_terms = self.intent_classifier.get_search_terms(user_query)

        print(f"🎯 Intenção detectada: {intent}")
        print(f"🔍 Termos de busca: {search_terms}")

        all_results = []
        for term in search_terms[:3]:
            term_results = self.search_single(term, k=2, min_similarity=0.15)
            all_results.extend(term_results)

        unique_results = {}
        for result in all_results:
            chunk_id = result['chunk_id']
            if (
                chunk_id not in unique_results
                or result['similarity'] > unique_results[chunk_id]['similarity']
            ):
                unique_results[chunk_id] = result

        final_results = sorted(
            unique_results.values(),
            key=lambda x: x['similarity'],
            reverse=True
        )[:k]

        natural_response = None
        if self.gemini_assistant and final_results:
            try:
                natural_response = self.gemini_assistant.generate_natural_response(
                    user_query, final_results
                )
                print("✅ Resposta gerada pelo Gemini")
            except Exception as e:
                print(f"⚠️  Erro no Gemini: {e}")
                natural_response = None

        return {
            'intent': intent,
            'recommended_functions': recommended_functions,
            'search_terms_used': search_terms[:3],
            'results': final_results,
            'natural_response': natural_response,
            'gemini_used': natural_response is not None
        }

    # ---------------------------------------------
    # Persistência
    # ---------------------------------------------
    def save(self, path: str = 'index_data'):
        import faiss

        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, f'{path}/faiss.index')
        self.chunks_df.write_parquet(f'{path}/chunks.parquet')

        print(f"💾 Índice salvo: {len(self.chunks_df)} chunks")

    def load(self, path: str = 'index_data'):
        import faiss

        self.index = faiss.read_index(f'{path}/faiss.index')
        self.chunks_df = pl.read_parquet(f'{path}/chunks.parquet')

        print(f"📁 Índice carregado: {len(self.chunks_df)} chunks")
