"""
Gerenciador de diretórios temporários para o video-encoder.

Este módulo contém a classe TempDirectoryManager que é responsável por
criar, gerenciar e limpar diretórios temporários usados para cópia de
arquivos remotos antes da conversão.
"""

import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple
import psutil


class TempDirectoryManager:
    """Gerenciador de diretórios temporários."""
    
    DEFAULT_PREFIX = "video_encoder_"
    
    def __init__(self, base_temp_dir: Optional[str] = None):
        """
        Inicializa o gerenciador de diretórios temporários.
        
        Args:
            base_temp_dir: Diretório base para arquivos temporários.
                          Se None, usa o diretório temporário do sistema.
        """
        if base_temp_dir:
            self.base_temp_dir = Path(base_temp_dir)
            self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Usa diretório temporário do sistema
            self.base_temp_dir = Path(tempfile.gettempdir()) / "video_encoder"
            self.base_temp_dir.mkdir(parents=True, exist_ok=True)
    
    def create_temp_directory(self, prefix: Optional[str] = None) -> str:
        """
        Cria um diretório temporário único.
        
        Args:
            prefix: Prefixo para o nome do diretório. Se None, usa DEFAULT_PREFIX.
            
        Returns:
            Caminho completo do diretório temporário criado.
        """
        if prefix is None:
            prefix = self.DEFAULT_PREFIX
        
        # Cria diretório com timestamp para garantir unicidade
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_dir_name = f"{prefix}{timestamp}"
        temp_dir_path = self.base_temp_dir / temp_dir_name
        
        temp_dir_path.mkdir(parents=True, exist_ok=True)
        
        return str(temp_dir_path)
    
    def get_available_space(self, path: Optional[str] = None) -> int:
        """
        Retorna espaço disponível em bytes no disco.
        
        Args:
            path: Caminho para verificar. Se None, usa base_temp_dir.
            
        Returns:
            Espaço disponível em bytes.
        """
        if path is None:
            path = str(self.base_temp_dir)
        
        try:
            usage = psutil.disk_usage(path)
            return usage.free
        except Exception:
            return 0
    
    def get_total_space(self, path: Optional[str] = None) -> int:
        """
        Retorna espaço total em bytes no disco.
        
        Args:
            path: Caminho para verificar. Se None, usa base_temp_dir.
            
        Returns:
            Espaço total em bytes.
        """
        if path is None:
            path = str(self.base_temp_dir)
        
        try:
            usage = psutil.disk_usage(path)
            return usage.total
        except Exception:
            return 0
    
    def get_used_space(self, path: Optional[str] = None) -> int:
        """
        Retorna espaço usado em bytes no disco.
        
        Args:
            path: Caminho para verificar. Se None, usa base_temp_dir.
            
        Returns:
            Espaço usado em bytes.
        """
        if path is None:
            path = str(self.base_temp_dir)
        
        try:
            usage = psutil.disk_usage(path)
            return usage.used
        except Exception:
            return 0
    
    def check_disk_space(self, required_gb: float, path: Optional[str] = None) -> Tuple[bool, float]:
        """
        Verifica se há espaço em disco suficiente.
        
        Args:
            required_gb: Espaço requerido em GB.
            path: Caminho para verificar. Se None, usa base_temp_dir.
            
        Returns:
            Tuple com (espaco_suficiente, espaco_disponivel_gb).
        """
        available_bytes = self.get_available_space(path)
        available_gb = available_bytes / (1024 ** 3)
        
        return (available_gb >= required_gb, available_gb)
    
    def cleanup(self, temp_dir: str) -> bool:
        """
        Remove um diretório temporário e seus conteúdos.
        
        Args:
            temp_dir: Caminho do diretório temporário a ser removido.
            
        Returns:
            True se removido com sucesso, False caso contrário.
        """
        try:
            temp_path = Path(temp_dir)
            
            # Verifica se o diretório está dentro do base_temp_dir por segurança
            try:
                temp_path.relative_to(self.base_temp_dir)
            except ValueError:
                # Diretório não está dentro do base_temp_dir
                return False
            
            if temp_path.exists():
                shutil.rmtree(temp_path)
                return True
            
            return False
        except Exception:
            return False
    
    def cleanup_old_directories(self, max_age_hours: int = 24) -> int:
        """
        Remove diretórios temporários antigos.
        
        Args:
            max_age_hours: Idade máxima em horas. Diretórios mais antigos serão removidos.
            
        Returns:
            Número de diretórios removidos.
        """
        removed_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        try:
            for item in self.base_temp_dir.iterdir():
                if not item.is_dir():
                    continue
                
                # Verifica se o nome do diretório começa com o prefixo
                if not item.name.startswith(self.DEFAULT_PREFIX):
                    continue
                
                # Obtém tempo de modificação do diretório
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    
                    if mtime < cutoff_time:
                        shutil.rmtree(item)
                        removed_count += 1
                except Exception:
                    # Se não conseguir obter mtime, ignora
                    continue
        except Exception:
            pass
        
        return removed_count
    
    def get_temp_directories(self) -> list:
        """
        Retorna lista de diretórios temporários existentes.
        
        Returns:
            Lista de caminhos de diretórios temporários.
        """
        temp_dirs = []
        
        try:
            for item in self.base_temp_dir.iterdir():
                if item.is_dir() and item.name.startswith(self.DEFAULT_PREFIX):
                    temp_dirs.append(str(item))
        except Exception:
            pass
        
        return sorted(temp_dirs)
    
    def get_directory_info(self, temp_dir: str) -> dict:
        """
        Obtém informações sobre um diretório temporário.
        
        Args:
            temp_dir: Caminho do diretório temporário.
            
        Returns:
            Dicionário com informações do diretório.
        """
        temp_path = Path(temp_dir)
        
        if not temp_path.exists():
            return {
                'exists': False,
                'path': temp_dir,
                'size_bytes': 0,
                'file_count': 0,
                'created_at': None,
                'modified_at': None
            }
        
        # Calcula tamanho total e contagem de arquivos
        total_size = 0
        file_count = 0
        
        for file_path in temp_path.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except Exception:
                    pass
        
        stat_info = temp_path.stat()
        
        return {
            'exists': True,
            'path': temp_dir,
            'size_bytes': total_size,
            'size_gb': total_size / (1024 ** 3),
            'file_count': file_count,
            'created_at': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        }
    
    def validate_temp_directory(self, temp_dir: str) -> Tuple[bool, str]:
        """
        Valida se um diretório temporário é válido e seguro.
        
        Args:
            temp_dir: Caminho do diretório temporário a validar.
            
        Returns:
            Tuple com (valido, mensagem_erro).
        """
        temp_path = Path(temp_dir)
        
        # Verifica se existe
        if not temp_path.exists():
            return (False, "Diretório não existe")
        
        # Verifica se é um diretório
        if not temp_path.is_dir():
            return (False, "Caminho não é um diretório")
        
        # Verifica se está dentro do base_temp_dir
        try:
            temp_path.relative_to(self.base_temp_dir)
        except ValueError:
            return (False, "Diretório não está no diretório temporário base")
        
        # Verifica permissões de escrita
        test_file = temp_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            return (False, "Sem permissão de escrita no diretório")
        except Exception:
            pass
        
        return (True, "Diretório válido")
