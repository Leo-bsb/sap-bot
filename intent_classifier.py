# intent_classifier.py
import re
from typing import Dict, List, Tuple

class IntentClassifier:
    def __init__(self):
        self.intent_patterns = {
            'conditional_logic': [
                r'(como|como usar|usar).*(condição|condicional|se|caso|if)',
                r'(transformação|transformar).*(condicional)',
                r'(quando|se).*(então|then)',
                r'(múltiplas|várias).*(condições|condição)'
            ],
            'data_lookup': [
                r'(como|como usar|usar).*(buscar|procurar|consultar|referência)',
                r'(tabela|tabela de).*(referência|lookup)',
                r'(join|junção).*(tabela)',
                r'(relacionar|associar).*(dados)'
            ],
            'data_validation': [
                r'(como|como usar|usar).*(validar|validação)',
                r'(verificar|checar).*(dados|informação)',
                r'(qualidade).*(dados)',
                r'(erro|inválido).*(dados)'
            ],
            'string_operations': [
                r'(como|como usar|usar).*(texto|string|cadeia)',
                r'(manipular|transformar).*(texto|string)',
                r'(concatenar|juntar).*(texto|palavras)',
                r'(extrair|pegar).*(parte|pedaço).*(texto)'
            ],
            'date_operations': [
                r'(como|como usar|usar).*(data|datahora|timestamp)',
                r'(calcular|somar|subtrair).*(data|dias)',
                r'(formato|formatar).*(data)',
                r'(data).*(atual|hoje|sistema)'
            ],
            'aggregation': [
                r'(como|como usar|usar).*(somar|total|média|médio|contar)',
                r'(agregação|agregar).*(dados)',
                r'(soma|total|média|contagem)',
                r'(group by|agrupar).*(dados)'
            ]
        }
        
        self.function_mapping = {
            'conditional_logic': ['decode', 'ifthenelse', 'case'],
            'data_lookup': ['lookup', 'lookup_ext', 'lookup_seq', 'join'],
            'data_validation': ['is_valid', 'is_number', 'is_date', 'match_pattern'],
            'string_operations': ['substr', 'concat', 'lower', 'upper', 'trim', 'replace'],
            'date_operations': ['add_days', 'date_diff', 'to_date', 'sysdate'],
            'aggregation': ['sum', 'avg', 'count', 'min', 'max']
        }
    
    def classify_intent(self, query: str) -> Tuple[str, List[str]]:
        """Classifica a intenção e retorna funções recomendadas"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    recommended_functions = self.function_mapping.get(intent, [])
                    return intent, recommended_functions
        
        # Se não encontrou padrão específico, busca geral
        return 'general_search', []
    
    def get_search_terms(self, query: str) -> List[str]:
        """Gera termos de busca baseados na intenção"""
        intent, recommended_functions = self.classify_intent(query)
        
        search_terms = [query]  # Termo original
        
        # Adiciona funções recomendadas
        search_terms.extend(recommended_functions)
        
        # Adiciona sinônimos baseados na intenção
        intent_synonyms = {
            'conditional_logic': ['conditional transformation', 'if else logic', 'case statement'],
            'data_lookup': ['data lookup', 'reference table', 'dimension lookup'],
            'data_validation': ['data validation', 'data quality', 'data cleansing'],
            'string_operations': ['string functions', 'text manipulation', 'string handling'],
            'date_operations': ['date functions', 'datetime operations', 'timestamp'],
            'aggregation': ['aggregate functions', 'group by operations', 'summary functions']
        }
        
        if intent in intent_synonyms:
            search_terms.extend(intent_synonyms[intent])
        
        return search_terms