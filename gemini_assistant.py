import os
import google.generativeai as genai
from typing import Dict, List

class GeminiAssistant:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Confirme o nome do modelo correto
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_natural_response(self, user_query: str, search_results: List[Dict], context: str = "") -> str:
        search_context = ""
        for i, result in enumerate(search_results[:3], 1):
            search_context += f"Resultado {i} (Similaridade: {result['similarity']:.3f}):\n{result['text']}\n\n"

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
"""

       try:
    response = self.model.generate(prompt)
    print(f"🟢 Resposta Gemini RAW: {response}")
    print(f"🟢 Resposta Gemini TEXT: {getattr(response, 'text', None)}")
    if hasattr(response, 'text') and response.text.strip():
        return response.text
    else:
        print("⚠️ Resposta Gemini está vazia ou inválida")
        return None
except Exception as e:
    print(f"❌ Erro ao gerar resposta com Gemini: {e}\nContexto:\n{search_context}")
    return None

    try:
        response = self.model.generate_text(prompt)
        return response.text
    except Exception as e:
        return f"❌ Erro ao gerar resposta com Gemini: {e}\n\nContexto:\n{search_context}"

    def generate_code_example(self, function_name: str, search_results: List[Dict]) -> str:
        search_context = "\n".join([f"Doc {i}: {r['text']}" for i, r in enumerate(search_results[:2], 1)])

        prompt = f"""
Com base na documentação do SAP Data Services abaixo, crie exemplos práticos em português para a função {function_name}:

DOCUMENTAÇÃO:
{search_context}

Crie em português:
1. Sintaxe completa da função
2. Exemplo básico de uso
3. Exemplo avançado com cenário real
4. Explicação dos parâmetros

Responda em português de forma clara e técnica:
"""

        try:
            response = self.model.generate_text(prompt)
            return response.text
        except Exception as e:
            return f"Erro ao gerar exemplo de código: {e}"
