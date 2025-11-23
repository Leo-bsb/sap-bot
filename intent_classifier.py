import re
from typing import List, Tuple


class IntentClassifier:
    """
    Classifica a intenção da pergunta do usuário em duas grandes famílias:
    
    1) Intenções relacionadas a SAP Data Services (ativam busca na documentação)
    2) Intenções gerais ou conversacionais (NÃO ativam busca)
    
    Essa separação é fundamental para permitir que o bot seja
    - Generalista quando necessário
    - Especialista quando apropriado
    """

    def __init__(self):
        # ----------------------------
        # INTENTS DE SAP DATA SERVICES
        # ----------------------------

        self.intent_patterns = {
            'conditional_logic': [
                r'(como|usar).*(condição|condicional|se|caso|if)',
                r'(transformação|transformar).*(condicional)',
                r'(quando|se).*(então|then)',
                r'(múltiplas|várias).*(condições)'
            ],
            'data_lookup': [
                r'(como|usar).*(buscar|procurar|lookup|referência)',
                r'(tabela).*(referência|lookup)',
                r'(join|junção)',
                r'(relacionar|associar).*(dados)'
            ],
            'data_validation': [
                r'(como|usar).*(validar)',
                r'(verificar|checar).*(dados)',
                r'(qualidade).*(dados)',
                r'(erro|inválido).*(dados)'
            ],
            'string_operations': [
                r'(como|usar).*(texto|string|cadeia)',
                r'(manipular|transformar).*(texto|string)',
                r'(concatenar|juntar).*(texto)',
                r'(extrair).*(texto)'
            ],
            'date_operations': [
                r'(como|usar).*(data|datahora|timestamp)',
                r'(calcular|somar|subtrair).*(data)',
                r'(formatar).*(data)',
                r'(data).*(hoje|atual|sistema)'
            ],
            'aggregation': [
                r'(como|usar).*(somar|média|contar)',
                r'(agregação|agrupar)',
                r'(soma|total|média|contagem)'
            ],

            # ------------------------------------
            # INTENTS NÃO-TÉCNICAS (GERAIS / CHAT)
            # ------------------------------------

            'small_talk': [
                r'^(oi|olá|ola|bom dia|boa tarde|boa noite)\b',
                r'(quem é você|quem é voce)',
                r'(qual seu nome)',
                r'(fale sobre você|sobre voce)',
                r'(você é um bot|voce é um bot)',
                r'(você é o gemini|voce é o gemini)',
                r'(como você funciona|como voce funciona)',
                r'(conte algo|me conte algo)',
                r'(piada|história)'
            ],

            'general_non_technical': [
                r'(dormir|sono|insônia|insônia)',
                r'(saúde|bem estar)',
                r'(receita|cozinhar)',
                r'(temperatura do modelo|temperatura)',
                r'(clima|previsão do tempo)',
                r'(motivação|carreira|estudo|vida)'
            ]
        }

        # Mapeamento de funções sugeridas (apenas para intenções técnicas)
        self.function_mapping = {
            'conditional_logic': ['decode', 'ifthenelse', 'case'],
            'data_lookup': ['lookup', 'lookup_ext', 'lookup_seq', 'join'],
            'data_validation': ['is_valid', 'is_number', 'is_date', 'match_pattern'],
            'string_operations': ['substr', 'concat', 'lower', 'upper', 'trim', 'replace'],
            'date_operations': ['add_days', 'date_diff', 'to_date', 'sysdate'],
            'aggregation': ['sum', 'avg', 'count', 'min', 'max']
        }

        # Intents que devem acionar documentação
        self.sap_intents = {
            'conditional_logic',
            'data_lookup',
            'data_validation',
            'string_operations',
            'date_operations',
            'aggregation'
        }

    # ------------------------------------------------------------
    # Função principal: classificar intenção da pergunta
    # ------------------------------------------------------------
    def classify_intent(self, query: str) -> Tuple[str, List[str]]:
        query_lower = query.lower()

        # 1) Primeiro, detectar small talk
        for pattern in self.intent_patterns['small_talk']:
            if re.search(pattern, query_lower):
                return 'small_talk', []

        # 2) Depois, detectar perguntas gerais não técnicas
        for pattern in self.intent_patterns['general_non_technical']:
            if re.search(pattern, query_lower):
                return 'general_non_technical', []

        # 3) Agora buscar intenções técnicas de SAP Data Services
        for intent in self.sap_intents:
            for pattern in self.intent_patterns[intent]:
                if re.search(pattern, query_lower):
                    return intent, self.function_mapping[intent]

        # 4) Se nada encaixar, considerar pergunta geral (NÃO técnica)
        return 'general_non_technical', []

    # ------------------------------------------------------------
    # Termos de busca (apenas para intenções SAP DS)
    # ------------------------------------------------------------
    def get_search_terms(self, query: str) -> List[str]:
        intent, recommended_functions = self.classify_intent(query)

        # Se não é SAP DS → sem documentação
        if intent not in self.sap_intents:
            return []

        search_terms = [query]  # termo original
        search_terms.extend(recommended_functions)

        return search_terms
