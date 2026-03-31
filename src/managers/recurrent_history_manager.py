import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading
import time


class RecurrentHistoryManager:
    """Gerenciador de histórico de processamento para pastas recorrentes."""
    
    def __init__(self, history_file_path: Optional[str] = None):
        """
        Inicializa o gerenciador de histórico.
        
        Args:
            history_file_path: Caminho para o arquivo de histórico (padrão: history.json)
        """
        self.history_file_path = Path(history_file_path) if history_file_path else Path(__file__).parent.parent / "history.json"
        self._lock = threading.RLock()  # Lock para thread safety
        self._load_history()
    
    def _load_history(self) -> None:
        """Carrega o histórico do arquivo."""
        with self._lock:
            if self.history_file_path.exists():
                try:
                    with open(self.history_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.history = data.get('history', [])
                except Exception:
                    self.history = []
            else:
                self.history = []
    
    def _save_history(self) -> bool:
        """Salva o histórico no arquivo."""
        with self._lock:
            try:
                # Garante que o diretório pai existe
                self.history_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.history_file_path, 'w', encoding='utf-8') as f:
                    json.dump({'history': self.history}, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"Erro ao salvar histórico: {e}")
                return False
    
    def add_entry(self, folder_id: str, input_path: str, output_path: str, status: str, 
                  started_at: datetime, completed_at: datetime, error_message: Optional[str] = None) -> str:
        """
        Adiciona uma entrada de histórico para um processamento.
        
        Args:
            folder_id: ID da pasta recorrente
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída
            status: Status do processamento ('completed', 'failed', etc.)
            started_at: Timestamp de início
            completed_at: Timestamp de conclusão
            error_message: Mensagem de erro (se falhou)
            
        Returns:
            ID da entrada criada
        """
        with self._lock:
            # Calcula duração em segundos
            duration_seconds = (completed_at - started_at).total_seconds()
            
            # Cria a entrada de histórico
            entry = {
                'id': str(uuid.uuid4()),
                'folder_id': folder_id,
                'input_path': input_path,
                'output_path': output_path,
                'status': status,
                'started_at': started_at.isoformat() + 'Z',
                'completed_at': completed_at.isoformat() + 'Z',
                'duration_seconds': duration_seconds,
                'error_message': error_message
            }
            
            # Adiciona à lista de histórico
            self.history.append(entry)
            
            # Salva no arquivo
            self._save_history()
            
            return entry['id']
    
    def get_history(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Retorna o histórico de processamentos para uma pasta específica.
        
        Args:
            folder_id: ID da pasta recorrente
            
        Returns:
            Lista de entradas de histórico para a pasta
        """
        with self._lock:
            return [entry for entry in self.history if entry['folder_id'] == folder_id]
    
    def get_stats(self, folder_id: str) -> Dict[str, Any]:
        """
        Retorna estatísticas de processamento para uma pasta específica.
        
        Args:
            folder_id: ID da pasta recorrente
            
        Returns:
            Dicionário com estatísticas
        """
        with self._lock:
            folder_history = self.get_history(folder_id)
            
            if not folder_history:
                return {
                    'total_processed': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'total_duration': 0,
                    'average_duration': 0,
                    'last_processed_at': None
                }
            
            # Conta sucessos e falhas
            success_count = sum(1 for entry in folder_history if entry['status'] == 'completed')
            failed_count = len(folder_history) - success_count
            
            # Calcula duração total e média
            total_duration = sum(entry['duration_seconds'] for entry in folder_history)
            average_duration = total_duration / len(folder_history) if folder_history else 0
            
            # Encontra a última data de processamento
            last_processed_at = max(
                (entry['completed_at'] for entry in folder_history),
                default=None
            )
            
            return {
                'total_processed': len(folder_history),
                'success_count': success_count,
                'failed_count': failed_count,
                'total_duration': total_duration,
                'average_duration': average_duration,
                'last_processed_at': last_processed_at
            }
    
    def get_recent_entries(self, folder_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna as entradas mais recentes de uma pasta específica.
        
        Args:
            folder_id: ID da pasta recorrente
            limit: Número máximo de entradas a retornar
            
        Returns:
            Lista de entradas ordenadas por data de conclusão (mais recentes primeiro)
        """
        with self._lock:
            folder_history = self.get_history(folder_id)
            
            # Ordena por data de conclusão (mais recentes primeiro)
            sorted_history = sorted(
                folder_history,
                key=lambda x: x['completed_at'],
                reverse=True
            )
            
            return sorted_history[:limit]
    
    def clear_history(self, folder_id: str) -> bool:
        """
        Limpa o histórico de uma pasta específica.
        
        Args:
            folder_id: ID da pasta recorrente
            
        Returns:
            True se limpo com sucesso, False caso contrário
        """
        with self._lock:
            initial_count = len(self.history)
            self.history = [entry for entry in self.history if entry['folder_id'] != folder_id]
            
            if len(self.history) != initial_count:
                return self._save_history()
            else:
                # Nenhuma entrada removida, mas isso não é um erro
                return True
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna estatísticas para todas as pastas recorrentes.
        
        Returns:
            Dicionário com estatísticas para cada pasta
        """
        with self._lock:
            all_folder_ids = set(entry['folder_id'] for entry in self.history)
            return {folder_id: self.get_stats(folder_id) for folder_id in all_folder_ids}
    
    def get_total_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas gerais de todos os processamentos.
        
        Returns:
            Dicionário com estatísticas gerais
        """
        with self._lock:
            if not self.history:
                return {
                    'total_processed': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'total_duration': 0,
                    'average_duration': 0,
                    'last_processed_at': None
                }
            
            success_count = sum(1 for entry in self.history if entry['status'] == 'completed')
            failed_count = len(self.history) - success_count
            total_duration = sum(entry['duration_seconds'] for entry in self.history)
            average_duration = total_duration / len(self.history) if self.history else 0
            
            last_processed_at = max(
                (entry['completed_at'] for entry in self.history),
                default=None
            )
            
            return {
                'total_processed': len(self.history),
                'success_count': success_count,
                'failed_count': failed_count,
                'total_duration': total_duration,
                'average_duration': average_duration,
                'last_processed_at': last_processed_at
            }