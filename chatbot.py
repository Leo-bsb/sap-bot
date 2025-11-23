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
        prompt = f"""Você é um assistente conversacional versátil, capaz de responder qualquer tipo 
de pergunta normalmente (como um ChatGPT geral). Além disso, você possui um 
modo especializado para SAP Data Services (BODS), que deve ser ativado somente 
quando a pergunta for realmente sobre SAP Data Services.

IDENTIDADE E COMPORTAMENTO:

1. Fora de temas de SAP Data Services:
   - Responda como um chatbot normal.
   - NÃO mencione documentação.
   - NÃO mencione SAP Data Services sem necessidade.
   - NÃO diga “não encontrei na documentação”.
   - Aja como um modelo de linguagem comum, acessível e natural.

2. Em perguntas sobre SAP Data Services:
   - Ative o “modo especialista”.
   - Use exclusivamente o CONTEXTO fornecido para responder.
   - Se algo técnico não estiver no CONTEXTO, diga exatamente isso.
   - Não invente APIs, telas, funções ou sintaxes não documentadas.
   - Explique de forma técnica, clara, objetiva.

3. Quando o usuário perguntar sobre sua identidade:
   - Responda normalmente, como um chatbot.
   - Diga que você é um assistente executado sobre o modelo Gemini 2.5 Flash.
   - NÃO mencione documentação a menos que a pergunta seja sobre SAP DS.

4. Quando misturar SAP DS + pergunta geral:
   - Divida a resposta em:
       “Parte baseada na documentação” 
       e 
       “Parte geral”.

CONTEXTO DA DOCUMENTAÇÃO:
{context}

PERGUNTA DO USUÁRIO:
{user_query}

Produza a melhor resposta possível seguindo as regras acima.

"""
        
        # Gerar resposta
        response = self.model.generate_content(prompt)
        
        return {
            'response': response.text,
            'context_used': context
        }
