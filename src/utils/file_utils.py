import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class FileUtils:
    """Utilitários para manipulação de arquivos."""
    
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg', '.ts', '.mts', '.m2ts'}
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.sub', '.ssa', '.vtt', '.idx', '.sup'}
    
    @staticmethod
    def is_video_file(path: str) -> bool:
        """Verifica se arquivo é vídeo."""
        return Path(path).suffix.lower() in FileUtils.VIDEO_EXTENSIONS
    
    @staticmethod
    def find_video_files(directory: str, recursive: bool = True) -> List[str]:
        """Encontra todos os arquivos de vídeo em diretório."""
        video_files: List[Path] = []
        path = Path(directory)
        
        if recursive:
            for ext in FileUtils.VIDEO_EXTENSIONS:
                video_files.extend(path.rglob(f"*{ext}"))
        else:
            for ext in FileUtils.VIDEO_EXTENSIONS:
                video_files.extend(path.glob(f"*{ext}"))
        
        return sorted([str(f) for f in video_files])
    
    @staticmethod
    def find_subtitle_files(directory: str) -> List[str]:
        """Encontra todos os arquivos de legenda em um diretório (não recursivo)."""
        subtitle_files: List[Path] = []
        path = Path(directory)
        for ext in FileUtils.SUBTITLE_EXTENSIONS:
            subtitle_files.extend(path.glob(f"*{ext}"))
        return sorted([str(f) for f in subtitle_files])

    @staticmethod
    def copy_subtitles_to_output(source_dir: str, output_dir: str, video_stem: Optional[str] = None) -> int:
        """Copia arquivos de legenda do diretório de origem para o de saída.
        Se video_stem for fornecido, copia apenas legendas que começam com esse stem.
        Retorna o número de arquivos copiados."""
        copied = 0
        subtitles = FileUtils.find_subtitle_files(source_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for sub_file in subtitles:
            sub_path = Path(sub_file)
            if video_stem and not sub_path.stem.startswith(video_stem):
                continue
            dest = Path(output_dir) / sub_path.name
            if FileUtils.safe_copy(sub_file, str(dest)):
                copied += 1
        return copied

    @staticmethod
    def calculate_hash(path: str, algorithm: str = 'sha256') -> Optional[str]:
        """Calcula hash do arquivo."""
        try:
            hash_func = hashlib.new(algorithm)
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def file_exists(path: str) -> bool:
        """Verifica se arquivo existe."""
        return Path(path).exists()
    
    @staticmethod
    def is_file_locked(path: str) -> bool:
        """Verifica se arquivo está bloqueado."""
        try:
            with open(path, 'a'):
                pass
            return False
        except IOError:
            return True
    
    @staticmethod
    def wait_for_file(path: str, timeout: int = 60, check_interval: float = 0.5) -> bool:
        """Aguarda arquivo estar disponível."""
        import time
        
        start = datetime.now()
        
        while (datetime.now() - start).total_seconds() < timeout:
            if Path(path).exists() and not FileUtils.is_file_locked(path):
                return True
            time.sleep(check_interval)
        
        return False
    
    @staticmethod
    def safe_delete(path: str) -> bool:
        """Exclui arquivo com segurança."""
        try:
            if Path(path).exists():
                Path(path).unlink()
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def safe_move(src: str, dst: str) -> bool:
        """Move arquivo com segurança."""
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_copy(src: str, dst: str) -> bool:
        """Copia arquivo com segurança."""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(path: str) -> Dict[str, Any]:
        """Retorna informações do arquivo."""
        try:
            stat = Path(path).stat()
            return {
                "path": path,
                "name": Path(path).name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": Path(path).suffix.lower(),
                "is_video": FileUtils.is_video_file(path)
            }
        except Exception:
            return {}
    
    @staticmethod
    def cleanup_partial_files(output_path: str, temp_extensions: Optional[List[str]] = None) -> int:
        """Limpa arquivos parciais/temporários."""
        if temp_extensions is None:
            temp_extensions = ['.tmp', '.temp', '.part', '.download']
        
        cleaned = 0
        output_path_obj = Path(output_path)
        output_dir = output_path_obj.parent
        output_name = output_path_obj.stem
        
        for ext in temp_extensions:
            for partial_file in output_dir.glob(f"{output_name}*{ext}"):
                if FileUtils.safe_delete(str(partial_file)):
                    cleaned += 1
        
        return cleaned
    
    @staticmethod
    def get_disk_free_space(path: str) -> int:
        """Retorna espaço livre em disco em bytes."""
        try:
            import psutil
            return psutil.disk_usage(path).free
        except ImportError:
            try:
                if os.name == 'nt':
                    import ctypes
                    free_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(path), None, None, ctypes.byref(free_bytes)
                    )
                    return free_bytes.value
                else:
                    stat = os.statvfs(path)  # type: ignore[attr-defined, misc]
                    return stat.f_bavail * stat.f_frsize
            except Exception:
                return 0
    
    @staticmethod
    def check_disk_space(path: str, required_gb: float) -> bool:
        """Verifica se há espaço em disco suficiente."""
        free_bytes = FileUtils.get_disk_free_space(path)
        required_bytes = required_gb * (1024 ** 3)
        return free_bytes >= required_bytes
    
    @staticmethod
    def generate_output_filename_for_profile(
        input_path: str,
        profile: Dict[str, Any],
        output_folder: str,
        preserve_structure: bool = True,
        naming_convention: str = "profile_suffix"
    ) -> str:
        """
        Gera nome de arquivo de output baseado no perfil.
        
        Args:
            input_path: Caminho do arquivo de entrada
            profile: Perfil de codificação
            output_folder: Pasta de saída
            preserve_structure: Preservar estrutura de diretórios
            naming_convention: Convenção de nomenclatura
                - "profile_suffix": filme_4k_hevc.mkv (default)
                - "profile_prefix": 4k_hevc_filme.mkv
                - "subfolder": 4k_hevc/filme.mkv
        
        Returns:
            Caminho completo do arquivo de output
        """
        input_file = Path(input_path)
        profile_suffix = FileUtils._get_profile_suffix(profile)
        
        if naming_convention == "profile_prefix":
            # Prefixo: {perfil}_{nome}.{ext}
            output_filename = f"{profile_suffix}_{input_file.stem}{input_file.suffix}"
            output_dir = Path(output_folder)
            
        elif naming_convention == "subfolder":
            # Subpasta: {perfil}/{nome}.{ext}
            output_filename = f"{input_file.stem}{input_file.suffix}"
            output_dir = Path(output_folder) / profile_suffix
            
        else:  # profile_suffix (default)
            # Sufixo: {nome}_{perfil}.{ext}
            output_filename = f"{input_file.stem}_{profile_suffix}{input_file.suffix}"
            output_dir = Path(output_folder)
        
        # Preservar estrutura de diretórios se opção estiver habilitada
        if preserve_structure and input_file.parent != input_file.parent.anchor:
            try:
                rel_path = input_file.parent.relative_to(input_file.parent.anchor)
                if str(rel_path) != '.':
                    output_dir = output_dir / rel_path
            except ValueError:
                pass
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir / output_filename)
    
    @staticmethod
    def _get_profile_suffix(profile: Dict[str, Any]) -> str:
        """
        Gera sufixo do perfil para nomenclatura.
        
        Args:
            profile: Perfil de codificação
            
        Returns:
            String de sufixo para nomenclatura
        """
        codec = profile.get('codec', 'unknown')
        resolution = profile.get('resolution', '')
        cq = profile.get('cq', '')
        
        # Extrair nome curto do codec
        codec_short = codec.replace('_nvenc', '').replace('_amf', '').replace('_qsv', '')
        
        parts = []
        
        # Adicionar resolução se disponível
        if resolution:
            parts.append(resolution)
        
        # Adicionar codec
        parts.append(codec_short)
        
        # Adicionar CQ se disponível
        if cq:
            parts.append(f'cq{cq}')
        
        # Se não houver partes, usar nome do perfil
        if not parts:
            return profile.get('name', 'profile').lower().replace(' ', '_')[:20]
        
        return '_'.join(parts)
    
    @staticmethod
    def estimate_output_size(
        input_size: int,
        profile: Dict[str, Any],
        duration_seconds: Optional[float] = None
    ) -> int:
        """
        Estima tamanho do output baseado no perfil.
        
        Args:
            input_size: Tamanho do arquivo de entrada em bytes
            profile: Perfil de codificação
            duration_seconds: Duração do vídeo em segundos (opcional)
            
        Returns:
            Tamanho estimado em bytes
        """
        if input_size == 0:
            return 0
        
        # Se perfil usa bitrate, calcular baseado na duração
        if profile.get('bitrate'):
            bitrate = FileUtils._parse_bitrate(profile['bitrate'])
            # Usar duração fornecida ou estimar baseada no tamanho
            if duration_seconds is None:
                # Estimativa grosseira: assume 1 hora para cada GB
                duration_seconds = 3600 * (input_size / (1024 ** 3))
            return int(bitrate * duration_seconds / 8)  # bits → bytes
        
        # Se perfil usa CQ, usar fator de compressão
        elif profile.get('cq'):
            cq = int(profile['cq'])
            # CQ menor = maior qualidade = maior arquivo
            # Fator de compressão: 0.1 (CQ 18) a 0.5 (CQ 28)
            compression_factor = 0.1 + ((cq - 18) / 10) * 0.4
            compression_factor = max(0.05, min(0.8, compression_factor))
            return int(input_size * compression_factor)
        
        # Fallback: estimativa conservadora (30% do original)
        return int(input_size * 0.3)
    
    @staticmethod
    def _parse_bitrate(bitrate_str: str) -> int:
        """
        Parse string de bitrate para bits/segundo.
        
        Exemplos:
            "10M" → 10000000
            "5000K" → 5000000
            "1M" → 1000000
        """
        bitrate_str = str(bitrate_str).upper().strip()
        multiplier = 1
        
        if bitrate_str.endswith('M'):
            multiplier = 1_000_000
            bitrate_str = bitrate_str[:-1]
        elif bitrate_str.endswith('K'):
            multiplier = 1_000
            bitrate_str = bitrate_str[:-1]
        
        try:
            return int(float(bitrate_str) * multiplier)
        except ValueError:
            return 5_000_000  # Fallback: 5M
