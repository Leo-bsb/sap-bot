import google.generativeai as genai
from typing import List, Dict
import logging


class GeminiAssistant:
    """
    Camada simples para gerar respostas usando Gemini.
    Usa generate_content() da API oficial.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logging.info(f"🟢 GeminiAssistant inicializado com modelo: {model_name}")
        except Exception as e:
            logging.error(f"❌ Falha ao configurar GeminiAssistant: {e}")
            raise e

    def generate_natural_response(
        self,
        user_query: str,
        search_results: List[Dict],
        context: str = ""
    ) -> str:
        """
        Gera resposta natural usando Gemini, com contexto dos embeddings.
        """

        # Montagem do contexto da busca
        search_context = ""
        for i, result in enumerate(search_results[:3], 1):
            similarity = result.get("similarity", 0)
            text = result.get("text", "")
            search_context += f"Resultado {i} (Similaridade: {similarity:.3f}):\n{text}\n\n"

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
{search_context}

PERGUNTA DO USUÁRIO:
{user_query}

Produza a melhor resposta possível seguindo as regras acima.


""".strip()

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                )
            )

            logging.info(f"🟢 Resposta bruta Gemini: {response}")

            # Ponto central da API: o texto final é response.text
            if hasattr(response, "text") and response.text:
                return response.text.strip()

            logging.warning("⚠️ Gemini retornou resposta vazia.")
            return "⚠️ O modelo não conseguiu gerar uma resposta adequada."

        except Exception as e:
            logging.error(
                f"❌ Erro ao gerar resposta com Gemini: {e}\n"
                f"Contexto da busca:\n{search_context}"
            )
            return f"Erro ao gerar resposta: {e}"
