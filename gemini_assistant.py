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
{search_context}

PERGUNTA DO USUÁRIO:
{user_query}

Agora produza a melhor resposta possível.

""".strip()

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
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
