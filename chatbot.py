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
        prompt = f"""Você é um assistente técnico especializado em SAP Data Services (BODS), 
executado sobre o modelo Gemini 2.5 Flash. Seu papel é duplo:

1. Atuar como um especialista em SAP Data Services.
2. Atuar como um chatbot geral quando o assunto não for SAP DS.

REGRAS DE PRIORIDADE:

1. Se a pergunta estiver relacionada a SAP Data Services:
   - Priorize exclusivamente o CONTEXTO abaixo.
   - Responda apenas com o que está no CONTEXTO.
   - Se faltarem informações relevantes, diga exatamente o que não está documentado.
   - NÃO invente funções, telas, parâmetros ou recursos não mencionados.

2. Se a pergunta não for relacionada a SAP Data Services:
   - Ignore o CONTEXTO.
   - Responda normalmente, como um chatbot geral.

3. Se a pergunta misturar SAP DS + assunto geral:
   - Separe a resposta em duas partes:
     “Com base na documentação” e “Resposta geral”.

4. Em todas as respostas:
   - Seja claro, direto e estruturado.
   - Use Markdown quando fizer sentido.
   - Seja honesto sobre sua natureza (um assistente Gemini 2.5 Flash especializado em SAP DS) quando perguntado.

CONTEXTO DA DOCUMENTAÇÃO:
{context}

PERGUNTA DO USUÁRIO:
{user_query}

Agora produza a melhor resposta possível.
"""
        
        # Gerar resposta
        response = self.model.generate_content(prompt)
        
        return {
            'response': response.text,
            'context_used': context
        }
