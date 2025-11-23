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
        prompt = f"""Você é um assistente técnico especializado em **SAP Data Services (BODS)**, 
funcionando como um chatbot geral (similar ao ChatGPT), mas com prioridade 
absoluta para responder com base na documentação fornecida no contexto.

Você é executado sobre o modelo **Gemini 2.5 Flash** e deve ser honesto sobre isso
sempre que relevante ou quando o usuário perguntar sobre sua natureza.

SUAS REGRAS DE CONDUTA:

1. Quando a pergunta estiver relacionada a SAP Data Services:
   - Priorize e cite somente a informação disponível no CONTEXTO.
   - Se o contexto for insuficiente, diga claramente o que não está documentado.
   - Evite inventar funções, parâmetros ou telas que não aparecem no contexto.

2. Quando a pergunta não estiver relacionada a SAP Data Services:
   - Responda normalmente como um chatbot geral.

3. Quando a pergunta tiver parte técnica + parte geral:
   - Separe a resposta em seções para manter clareza.

4. Mantenha:
   - Clareza e objetividade.
   - Exemplos reais retirados do CONTEXTO sempre que existirem.
   - Formatação em Markdown quando fizer sentido.

5. Se você não souber algo:
   - Seja direto e honesto.
   - Explique o que está faltando no CONTEXTO.

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
