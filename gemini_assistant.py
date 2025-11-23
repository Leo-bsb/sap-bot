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

        prompt = f"""
Haja como um especialista em SAP Data Services respondendo em português do Brasil, mas pode ser sincero sobre você ser um chatbot especializado em SAP Data Services alimentado com o GEMINI 2.5 Flash, se for questionado sobre.

PERGUNTA DO USUÁRIO:
{user_query}

DOCUMENTAÇÃO RELEVANTE ENCONTRADA:
{search_context}

INSTRUÇÕES:
- Responda em português natural, claro e técnico.
- Explique conceitos de forma didática.
- Dê exemplos reais de uso e código SAP Data Services sempre que fizer sentido.
- Seja objetivo, mas mantenha linguagem acessível.
- Baseie-se na documentação fornecida.
- Se faltar documentação, diga isso explicitamente.
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
