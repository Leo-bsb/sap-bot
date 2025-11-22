# document_preprocessor.py
import re
import polars as pl
from pathlib import Path
from typing import List, Dict
import tqdm

class DocumentPreprocessor:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Chunks menores para melhor precisão
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def process_document(self, file_path: str) -> pl.DataFrame:
        """Processa o documento em chunks menores"""
        print(f"📄 Lendo documento: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Limpa o conteúdo
        content = self._clean_text(content)
        
        # Divide em seções usando padrões da documentação SAP
        sections = self._split_into_sections(content)
        
        # Processa cada seção em chunks
        all_chunks = []
        chunk_id = 0
        
        for section_name, section_text in sections:
            section_chunks = self._split_section_into_chunks(section_text, section_name)
            
            for chunk_text in section_chunks:
                if len(chunk_text.strip()) > 100:  # Só adiciona chunks significativos
                    all_chunks.append({
                        'chunk_id': chunk_id,
                        'text': chunk_text.strip(),
                        'section': section_name,
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split())
                    })
                    chunk_id += 1
        
        print(f"✅ Criados {len(all_chunks)} chunks de {len(sections)} seções")
        return pl.DataFrame(all_chunks)
    
    def _split_into_sections(self, content: str) -> List[tuple]:
        """Divide o conteúdo em seções lógicas"""
        sections = []
        
        # Padrões comuns em documentação SAP
        patterns = [
            r'(\d+\.\d+(?:\.\d+)*\s+[^\n]+)',  # 6.1.3.32 decrypt_aes
            r'(##+\s+[^\n]+)',  # ## Título
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+function)',  # Nome da função
        ]
        
        current_section = "Introdução"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Verifica se é início de nova seção
            is_section = False
            section_name = current_section
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    section_name = match.group(1).strip()
                    is_section = True
                    break
            
            if is_section and current_content:
                # Salva a seção anterior
                sections.append((current_section, '\n'.join(current_content)))
                current_content = []
                current_section = section_name
            
            current_content.append(line)
        
        # Adiciona a última seção
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _split_section_into_chunks(self, text: str, section_name: str) -> List[str]:
        """Divide uma seção em chunks menores"""
        # Primeiro tenta dividir por parágrafos
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Se o parágrafo sozinho for muito grande, divide em sentenças
            if len(paragraph) > self.chunk_size:
                sentences = self._split_into_sentences(paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                        chunks.append(current_chunk)
                        # Mantém overlap com as últimas sentenças
                        overlap_sentences = self._get_overlap_sentences(current_chunk)
                        current_chunk = overlap_sentences + " " + sentence
                    else:
                        current_chunk += " " + sentence
            else:
                if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = paragraph
                else:
                    current_chunk += " " + paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Divide texto em sentenças de forma inteligente"""
        # Divide por pontos que não são abreviações
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_sentences(self, text: str) -> str:
        """Pega as últimas sentenças para overlap"""
        sentences = self._split_into_sentences(text)
        overlap_text = ""
        
        for sentence in reversed(sentences):
            if len(overlap_text) + len(sentence) <= self.overlap:
                overlap_text = sentence + " " + overlap_text
            else:
                break
        
        return overlap_text.strip()
    
    def _clean_text(self, text: str) -> str:
        """Limpa o texto"""
        # Remove múltiplos espaços e quebras de linha
        text = re.sub(r'\s+', ' ', text)
        # Remove caracteres especiais problemáticos
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        return text.strip()