# ============= chatbot.py =============
import google.generativeai as genai

class SAPChatbot:
    def __init__(self, api_key: str, embedding_manager: EmbeddingManager):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.emb_manager = embedding_manager
        self.chat_history = []
    
    def get_context(self, query: str, k: int = 5) -> str:
        """Recupera contexto relevante"""
        results = self.emb_manager.search(query, k)
        
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"[Fonte {i+1}]\n{result['text']}\n")
        
        return "\n".join(context_parts)
    
    def generate_response(self, user_query: str) -> Dict:
        """Gera resposta usando RAG"""
        # Recuperar contexto
        context = self.get_context(user_query)
        
        # Criar prompt
        prompt = f"""Você é um assistente especializado em SAP Data Services ECC. 
        
Use APENAS as informações fornecidas abaixo para responder. Se a informação não estiver presente, diga que não encontrou na documentação.

CONTEXTO DA DOCUMENTAÇÃO:
{context}

PERGUNTA DO USUÁRIO:
{user_query}

INSTRUÇÕES:
- Responda de forma clara e objetiva
- Use exemplos do contexto quando disponíveis
- Se não souber, seja honesto
- Formate a resposta em markdown quando apropriado

RESPOSTA:"""
        
        # Gerar resposta
        response = self.model.generate_content(prompt)
        
        return {
            'response': response.text,
            'context_used': context
        }
