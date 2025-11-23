import logging

class GeminiAssistant:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # confirme nome do modelo

    def generate_natural_response(self, user_query: str, search_results: List[Dict], context: str = "") -> str:
        search_context = ""
        for i, result in enumerate(search_results[:3], 1):
            similarity = result.get('similarity', 0)
            text = result.get('text', '')
            search_context += f"Resultado {i} (Similaridade: {similarity:.3f}):\n{text}\n\n"

        prompt = f"""
Você é um especialista em SAP Data Services respondendo em português do Brasil.

PERGUNTA DO USUÁRIO: {user_query}

CONTEXTO DA DOCUMENTAÇÃO ENCONTRADA:
{search_context}

INSTRUÇÕES:
1. Responda em português natural, claro e técnico
2. Explique conceitos de forma didática
3. Forneça exemplos práticos de código SAP Data Services
4. Seja objetivo mas com linguagem acessível
5. Baseie-se na documentação fornecida
6. Inclua sintaxe e exemplos reais de uso
7. Se a documentação for insuficiente, seja honesto

Responda diretamente em português de forma natural:
""".strip()

        try:
            response = self.model.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=6144
            )
            logging.info(f"🟢 Resposta Gemini RAW: {response}")

            text = None
            if hasattr(response, 'candidates') and response.candidates:
                text = response.candidates[0].output
                logging.info(f"🟢 Resposta Gemini TEXT: {text}")

            if text and text.strip():
                return text.strip()
            else:
                logging.warning("⚠️ Resposta Gemini está vazia ou inválida")
                return "⚠️ Não foi possível gerar uma resposta válida."

        except Exception as e:
            logging.error(f"❌ Erro ao gerar resposta com Gemini: {e}\nContexto:\n{search_context}")
            return f"Erro ao gerar resposta: {e}"
