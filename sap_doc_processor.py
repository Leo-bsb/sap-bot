import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import polars as pl
import pymupdf  # PyMuPDF
from datetime import datetime
from tqdm import tqdm

class SAPDocumentProcessor:
    def __init__(
        self, 
        pdf_path: str,
        output_dir: str = "data/processed",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def deep_diagnose_pdf(self) -> Dict:
        """
        Diagnóstico completo do PDF usando múltiplas abordagens
        """
        print("🔍 DIAGNÓSTICO COMPLETO DO PDF")
        print("=" * 50)
        
        results = {
            "file_info": {},
            "pymupdf_analysis": {},
            "alternative_methods": []
        }
        
        # Informações básicas do arquivo
        file_stat = os.stat(self.pdf_path)
        results["file_info"] = {
            "file_size_mb": file_stat.st_size / (1024 * 1024),
            "file_path": self.pdf_path,
            "exists": os.path.exists(self.pdf_path)
        }
        
        print(f"📁 Tamanho do arquivo: {results['file_info']['file_size_mb']:.2f} MB")
        
        # Análise com PyMuPDF
        try:
            doc = pymupdf.open(self.pdf_path)
            results["pymupdf_analysis"] = {
                "page_count": len(doc),
                "is_encrypted": doc.is_encrypted,
                "metadata": dict(doc.metadata),
                "can_access_pages": True,
                "error": None
            }
            doc.close()
            print(f"✅ PyMuPDF - Páginas: {len(doc)}, Criptografado: {doc.is_encrypted}")
            
        except Exception as e:
            results["pymupdf_analysis"] = {
                "page_count": 0,
                "is_encrypted": False,
                "metadata": {},
                "can_access_pages": False,
                "error": str(e)
            }
            print(f"❌ PyMuPDF erro: {e}")
        
        # Tenta métodos alternativos
        results["alternative_methods"] = self._try_all_extraction_methods()
        
        return results
    
    def _try_all_extraction_methods(self) -> List[Dict]:
        """Tenta todos os métodos de extração possíveis"""
        methods = []
        
        # Método 1: PyMuPDF com diferentes parâmetros
        for params in [
            {"name": "standard", "kwargs": {}},
            {"name": "repair_mode", "kwargs": {"garbage": 4, "deflate": True, "clean": True}},
            {"name": "weak_encryption", "kwargs": {"password": ""}}
        ]:
            try:
                doc = pymupdf.open(self.pdf_path, **params["kwargs"])
                page_count = len(doc)
                methods.append({
                    "method": f"pymupdf_{params['name']}",
                    "success": True,
                    "page_count": page_count,
                    "error": None
                })
                doc.close()
            except Exception as e:
                methods.append({
                    "method": f"pymupdf_{params['name']}",
                    "success": False,
                    "page_count": 0,
                    "error": str(e)
                })
        
        # Método 2: Tentar extrair texto página por página mesmo com erro
        methods.append(self._try_page_by_page_extraction())
        
        return methods
    
    def _try_page_by_page_extraction(self) -> Dict:
        """Tenta extrair página por página mesmo com possíveis erros"""
        try:
            doc = pymupdf.open(self.pdf_path)
            successful_pages = 0
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        successful_pages += 1
                except:
                    continue
            
            doc.close()
            
            return {
                "method": "page_by_page_recovery",
                "success": successful_pages > 0,
                "page_count": successful_pages,
                "total_pages": total_pages,
                "success_rate": (successful_pages / total_pages) * 100 if total_pages > 0 else 0,
                "error": None
            }
            
        except Exception as e:
            return {
                "method": "page_by_page_recovery", 
                "success": False,
                "page_count": 0,
                "total_pages": 0,
                "success_rate": 0,
                "error": str(e)
            }
    
    def extract_with_fallback_strategy(self) -> List[Dict]:
        """
        Estratégia robusta de extração com múltiplos fallbacks
        """
        print("\n🔄 ESTRATÉGIA DE EXTRAÇÃO ROBUSTA")
        print("=" * 40)
        
        # Primeiro tenta o método mais agressivo de recuperação
        pages_data = self._extract_with_aggressive_recovery()
        
        if pages_data:
            print(f"✅ Método agressivo recuperou {len(pages_data)} páginas")
            return pages_data
        
        # Se não funcionar, tenta com outras bibliotecas
        print("🔄 Tentando com pdfplumber...")
        pages_data = self._try_pdfplumber()
        
        if pages_data:
            print(f"✅ pdfplumber recuperou {len(pages_data)} páginas")
            return pages_data
        
        # Última tentativa: PyPDF2
        print("🔄 Tentando com PyPDF2...")
        pages_data = self._try_pypdf2()
        
        if pages_data:
            print(f"✅ PyPDF2 recuperou {len(pages_data)} páginas")
            return pages_data
        
        print("❌ Nenhum método conseguiu extrair texto")
        return []
    
    def _extract_with_aggressive_recovery(self) -> List[Dict]:
        """Tenta extrair com configurações agressivas de recuperação"""
        try:
            # Tenta abrir com todos os parâmetros de reparo possíveis
            doc = pymupdf.open(
                self.pdf_path,
                garbage=4,
                deflate=True,
                clean=True,
                repair=True
            )
            
            pages_data = []
            successful_pages = 0
            
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    
                    # Tenta diferentes métodos de extração por página
                    text = self._extract_text_from_page(page)
                    
                    if text and text.strip():
                        pages_data.append({
                            'page_number': page_num + 1,
                            'text': self._clean_text(text),
                            'char_count': len(text),
                            'extraction_method': 'aggressive_recovery'
                        })
                        successful_pages += 1
                        
                except Exception as e:
                    # Continua para a próxima página mesmo com erro
                    continue
            
            doc.close()
            return pages_data
            
        except Exception as e:
            print(f"❌ Método agressivo falhou: {e}")
            return []
    
    def _extract_text_from_page(self, page) -> str:
        """Tenta múltiplos métodos de extração por página"""
        methods = [
            lambda p: p.get_text(),
            lambda p: p.get_text("text"),
            lambda p: p.get_text("words"),
            lambda p: p.get_text("blocks"),
            lambda p: p.get_text("dict")
        ]
        
        for method in methods:
            try:
                result = method(page)
                if isinstance(result, str) and result.strip():
                    return result
                elif isinstance(result, list) and result:
                    # Processa resultados estruturados
                    if method == methods[2]:  # words
                        words = [word[4] for word in result if len(word) > 4]
                        return " ".join(words)
                    elif method == methods[3]:  # blocks
                        texts = [block[4] for block in result if len(block) > 4]
                        return "\n".join(texts)
            except:
                continue
        
        return ""
    
    def _try_pdfplumber(self) -> List[Dict]:
        """Tenta extrair com pdfplumber (biblioteca alternativa)"""
        try:
            import pdfplumber
            
            pages_data = []
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            pages_data.append({
                                'page_number': page_num + 1,
                                'text': self._clean_text(text),
                                'char_count': len(text),
                                'extraction_method': 'pdfplumber'
                            })
                    except:
                        continue
            
            return pages_data
            
        except ImportError:
            print("📚 pdfplumber não instalado. Instale com: pip install pdfplumber")
            return []
        except Exception as e:
            print(f"❌ pdfplumber falhou: {e}")
            return []
    
    def _try_pypdf2(self) -> List[Dict]:
        """Tenta extrair com PyPDF2 (outra biblioteca alternativa)"""
        try:
            import PyPDF2
            
            pages_data = []
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text and text.strip():
                            pages_data.append({
                                'page_number': page_num + 1,
                                'text': self._clean_text(text),
                                'char_count': len(text),
                                'extraction_method': 'pypdf2'
                            })
                    except:
                        continue
            
            return pages_data
            
        except ImportError:
            print("📚 PyPDF2 não instalado. Instale com: pip install pypdf2")
            return []
        except Exception as e:
            print(f"❌ PyPDF2 falhou: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto extraído"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        return text.strip()
    
    def create_chunks(self, pages_data: List[Dict]) -> List[Dict]:
        """Divide o texto em chunks com sobreposição"""
        pages_with_content = [p for p in pages_data if p['text'].strip()]
        
        if not pages_with_content:
            print("⚠️  Nenhuma página com conteúdo para criar chunks")
            return []
            
        print(f"\n🔪 Criando chunks (tamanho: {self.chunk_size}, overlap: {self.chunk_overlap})...")
        chunks = []
        chunk_id = 0
        
        for page_data in tqdm(pages_with_content, desc="Criando chunks"):
            text = page_data['text']
            page_num = page_data['page_number']
            
            sentences = self._split_into_sentences(text)
            current_chunk = ""
            current_sentences = []
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                    chunks.append({
                        'chunk_id': chunk_id,
                        'text': current_chunk.strip(),
                        'page_number': page_num,
                        'char_count': len(current_chunk),
                        'sentence_count': len(current_sentences)
                    })
                    chunk_id += 1
                    
                    overlap_text = self._get_overlap_text(current_sentences)
                    current_chunk = overlap_text + " " + sentence
                    current_sentences = [sentence]
                else:
                    current_chunk += " " + sentence
                    current_sentences.append(sentence)
            
            if current_chunk.strip():
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': current_chunk.strip(),
                    'page_number': page_num,
                    'char_count': len(current_chunk),
                    'sentence_count': len(current_sentences)
                })
                chunk_id += 1
        
        print(f"✅ Criados {len(chunks)} chunks")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, sentences: List[str]) -> str:
        overlap_text = ""
        for sentence in reversed(sentences):
            if len(overlap_text) + len(sentence) <= self.chunk_overlap:
                overlap_text = sentence + " " + overlap_text
            else:
                break
        return overlap_text.strip()
    
    def save_chunks_to_parquet(self, chunks: List[Dict]) -> Optional[str]:
        if not chunks:
            print("⚠️  Nenhum chunk para salvar")
            return None
            
        print(f"\n💾 Salvando chunks em formato Parquet...")
        
        df = pl.DataFrame(chunks)
        df = df.with_columns([
            pl.lit(datetime.now().isoformat()).alias('processed_at'),
            pl.lit(self.pdf_path).alias('source_file')
        ])
        
        output_path = self.output_dir / "sap_chunks.parquet"
        df.write_parquet(output_path)
        
        print(f"✅ Chunks salvos em: {output_path}")
        return str(output_path)
    
    def process(self) -> Optional[str]:
        """Executa o pipeline completo de processamento"""
        start_time = datetime.now()
        print("🚀 Iniciando processamento da documentação SAP Data Services")
        print("=" * 60)
        
        try:
            # Primeiro faz diagnóstico completo
            diagnosis = self.deep_diagnose_pdf()
            
            # Salva diagnóstico
            diag_path = self.output_dir / "pdf_diagnosis.json"
            with open(diag_path, 'w', encoding='utf-8') as f:
                json.dump(diagnosis, f, indent=2, ensure_ascii=False)
            print(f"📋 Diagnóstico salvo em: {diag_path}")
            
            # Extrai texto com estratégia robusta
            pages_data = self.extract_with_fallback_strategy()
            
            if not pages_data:
                print("\n❌ Nenhum conteúdo extraído após todas as tentativas.")
                print("\n🔧 SOLUÇÕES ALTERNATIVAS:")
                print("1. Instale bibliotecas alternativas:")
                print("   pip install pdfplumber pypdf2")
                print("2. Converta o PDF para texto usando ferramentas do sistema:")
                print("   - No Linux: pdftotext arquivo.pdf")
                print("   - Usando Python: subprocess.run(['pdftotext', 'arquivo.pdf'])")
                print("3. Use o Adobe Reader para exportar como texto")
                return None
            
            # Cria chunks
            chunks = self.create_chunks(pages_data)
            
            if not chunks:
                print("❌ Nenhum chunk criado.")
                return None
            
            # Salva em Parquet
            parquet_path = self.save_chunks_to_parquet(chunks)
            
            # Estatísticas
            pages_with_content = [p for p in pages_data if p['text'].strip()]
            print(f"\n📊 RESUMO: {len(pages_with_content)} páginas com conteúdo -> {len(chunks)} chunks")
            
            elapsed = datetime.now() - start_time
            print(f"\n⏱️  Tempo total: {elapsed.total_seconds():.2f} segundos")
            print(f"✅ Processamento concluído com sucesso!")
            
            return parquet_path
            
        except Exception as e:
            print(f"\n❌ Erro durante o processamento: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# Exemplo de uso
if __name__ == "__main__":
    PDF_PATH = "data/raw/ds_2025_reference_en.pdf"
    OUTPUT_DIR = "data/processed"
    
    # Verifica se o PDF existe
    if not os.path.exists(PDF_PATH):
        print(f"❌ Arquivo PDF não encontrado: {PDF_PATH}")
        exit(1)
    
    processor = SAPDocumentProcessor(
        pdf_path=PDF_PATH,
        output_dir=OUTPUT_DIR,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    output_file = processor.process()
    
    if output_file:
        print(f"\n🎉 Arquivo processado disponível em: {output_file}")
        try:
            df = pl.read_parquet(output_file)
            print(f"Total de chunks carregados: {len(df)}")
            print("\nPrimeiros 3 chunks:")
            print(df.head(3).select(['chunk_id', 'page_number', 'char_count']))
        except Exception as e:
            print(f"Erro ao carregar chunks: {e}")
    else:
        print("\n❌ Processamento falhou.")