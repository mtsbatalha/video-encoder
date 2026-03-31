"""
Multi-Profile Conversion Manager

Gerenciador de conversões múltiplas com vários perfis simultâneos.
Permite criar jobs para combinações de arquivos × perfis em lote.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .profile_manager import ProfileManager
from .job_manager import JobManager
from .queue_manager import QueueManager, QueuePriority


class NamingConvention(Enum):
    """Convenções de nomenclatura para arquivos de output."""
    PROFILE_SUFFIX = "profile_suffix"  # filme_4k_hevc.mkv
    PROFILE_PREFIX = "profile_prefix"  # 4k_hevc_filme.mkv
    SUBFOLDER = "subfolder"  # 4k_hevc/filme.mkv


@dataclass
class PlannedJob:
    """Job planejado para conversão."""
    input_path: str
    output_path: str
    profile_id: str
    profile_name: str
    estimated_output_size: int  # bytes
    priority: QueuePriority = QueuePriority.NORMAL
    group_id: Optional[str] = None  # Para agrupar jobs relacionados
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionPlan:
    """Plano de conversão multi-perfil."""
    input_files: List[str]
    profiles: List[Dict[str, Any]]
    total_jobs: int
    jobs: List[PlannedJob]
    estimated_total_size: int  # bytes
    created_at: str
    options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte plano para dicionário."""
        return {
            "input_files": self.input_files,
            "profiles": [{"id": p["id"], "name": p["name"]} for p in self.profiles],
            "total_jobs": self.total_jobs,
            "estimated_total_size_gb": self.estimated_total_size / (1024 ** 3),
            "created_at": self.created_at,
            "options": self.options
        }


class MultiProfileConversionManager:
    """
    Gerenciador de conversões multi-perfil.
    
    Permite selecionar múltiplos perfis e criar automaticamente
    jobs para cada combinação de arquivo × perfil.
    """
    
    def __init__(
        self,
        profile_manager: ProfileManager,
        job_manager: JobManager,
        queue_manager: QueueManager
    ):
        """
        Inicializa o gerenciador.
        
        Args:
            profile_manager: Gerenciador de perfis
            job_manager: Gerenciador de jobs
            queue_manager: Gerenciador de fila
        """
        self.profile_mgr = profile_manager
        self.job_mgr = job_manager
        self.queue_mgr = queue_manager
    
    def generate_conversion_plan(
        self,
        input_files: List[str],
        profile_ids: List[str],
        output_folder: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ConversionPlan:
        """
        Gera plano de conversão sem criar jobs.
        
        Args:
            input_files: Lista de arquivos de entrada
            profile_ids: Lista de IDs de perfis
            output_folder: Pasta de saída
            options: Opções adicionais:
                - preserve_structure: Preservar estrutura de diretórios (default: True)
                - naming_convention: Convenção de nomenclatura (default: profile_suffix)
        
        Returns:
            Objeto ConversionPlan
        """
        options = options or {}
        
        # 1. Carregar perfis
        profiles = []
        for profile_id in profile_ids:
            profile = self.profile_mgr.get_profile(profile_id)
            if profile:
                profiles.append(profile)
        
        if not profiles:
            raise ValueError("Nenhum perfil válido encontrado")
        
        # 2. Gerar jobs planejados
        planned_jobs: List[PlannedJob] = []
        total_size = 0
        
        for input_file in input_files:
            input_path = Path(input_file)
            
            for profile in profiles:
                output_path = self._generate_output_path(
                    input_file, profile, output_folder, options
                )
                estimated_size = self._estimate_output_size(input_file, profile)
                
                planned_jobs.append(PlannedJob(
                    input_path=input_file,
                    output_path=output_path,
                    profile_id=profile['id'],
                    profile_name=profile['name'],
                    estimated_output_size=estimated_size,
                    priority=QueuePriority.NORMAL,
                    group_id=input_path.stem,
                    metadata={
                        "input_size": self._get_file_size(input_file),
                        "codec": profile.get('codec', ''),
                        "resolution": profile.get('resolution', '')
                    }
                ))
                
                total_size += estimated_size
        
        return ConversionPlan(
            input_files=input_files,
            profiles=profiles,
            total_jobs=len(planned_jobs),
            jobs=planned_jobs,
            estimated_total_size=total_size,
            created_at=datetime.now().isoformat(),
            options=options
        )
    
    def create_jobs_for_multiple_profiles(
        self,
        input_files: List[str],
        profile_ids: List[str],
        output_folder: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Cria jobs para múltiplos perfis e adiciona à fila.
        
        Args:
            input_files: Lista de arquivos de entrada
            profile_ids: Lista de IDs de perfis
            output_folder: Pasta de saída
            options: Opções adicionais
            
        Returns:
            Lista de jobs criados
        """
        options = options or {}
        jobs_created: List[Dict[str, Any]] = []
        
        for input_file in input_files:
            input_path = Path(input_file)
            
            for profile_id in profile_ids:
                profile = self.profile_mgr.get_profile(profile_id)
                if not profile:
                    continue
                
                output_path = self._generate_output_path(
                    input_file, profile, output_folder, options
                )
                
                # Criar job
                job_id = self.job_mgr.create_job(
                    input_path=input_file,
                    output_path=output_path,
                    profile_id=profile_id,
                    profile_name=profile['name']
                )
                
                # Adicionar à fila
                self.queue_mgr.add_to_queue(
                    job_id=job_id,
                    input_path=input_file,
                    output_path=output_path,
                    profile=profile,
                    priority=QueuePriority.NORMAL
                )
                
                jobs_created.append({
                    'job_id': job_id,
                    'input_path': input_file,
                    'output_path': output_path,
                    'profile_id': profile_id,
                    'profile_name': profile['name'],
                    'group_id': input_path.stem
                })
        
        return jobs_created
    
    def validate_profiles_compatibility(
        self,
        profile_ids: List[str]
    ) -> Tuple[bool, str]:
        """
        Valida se perfis são compatíveis entre si.
        
        Args:
            profile_ids: Lista de IDs de perfis
            
        Returns:
            Tuple (é_compatível, mensagem)
        """
        if not profile_ids:
            return (False, "Nenhum perfil selecionado")
        
        if len(profile_ids) == 1:
            return (True, "Perfil único selecionado")
        
        profiles = []
        for profile_id in profile_ids:
            profile = self.profile_mgr.get_profile(profile_id)
            if not profile:
                return (False, f"Perfil não encontrado: {profile_id}")
            profiles.append(profile)
        
        # Verificar duplicatas
        profile_names = [p['name'] for p in profiles]
        if len(profile_names) != len(set(profile_names)):
            return (False, "Perfis duplicados selecionados")
        
        # Verificar conflitos de codec (opcional - permite combinações)
        # Por enquanto, permitimos qualquer combinação de perfis
        
        return (True, f"{len(profiles)} perfis compatíveis selecionados")
    
    def get_plan_summary(self, plan: ConversionPlan) -> Dict[str, Any]:
        """
        Retorna resumo formatado do plano.
        
        Args:
            plan: Plano de conversão
            
        Returns:
            Dicionário com resumo formatado
        """
        # Agrupar jobs por arquivo
        from collections import defaultdict
        jobs_by_file = defaultdict(list)
        for job in plan.jobs:
            jobs_by_file[job.input_path].append(job)
        
        # Calcular estatísticas
        total_input_size = sum(job.metadata.get('input_size', 0) for job in plan.jobs)
        
        return {
            "total_files": len(plan.input_files),
            "total_profiles": len(plan.profiles),
            "total_jobs": plan.total_jobs,
            "estimated_output_size_gb": plan.estimated_total_size / (1024 ** 3),
            "estimated_input_size_gb": total_input_size / (1024 ** 3),
            "compression_ratio": plan.estimated_total_size / total_input_size if total_input_size > 0 else 0,
            "jobs_per_file": {
                Path(k).name: len(v) for k, v in jobs_by_file.items()
            }
        }
    
    def _generate_output_path(
        self,
        input_file: str,
        profile: Dict[str, Any],
        output_folder: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Gera caminho de output único para arquivo + perfil.
        
        Args:
            input_file: Caminho do arquivo de entrada
            profile: Perfil de codificação
            output_folder: Pasta de saída
            options: Opções de nomenclatura
            
        Returns:
            Caminho completo do arquivo de output
        """
        options = options or {}
        input_path = Path(input_file)
        
        # Obter convenção de nomenclatura
        naming = options.get('naming_convention', NamingConvention.PROFILE_SUFFIX.value)
        
        # Gerar sufixo do perfil
        profile_suffix = self._get_profile_suffix(profile)
        
        if naming == NamingConvention.PROFILE_PREFIX.value:
            # Prefixo: {perfil}_{nome}.{ext}
            output_filename = f"{profile_suffix}_{input_path.stem}{input_path.suffix}"
            output_dir = Path(output_folder)
            
        elif naming == NamingConvention.SUBFOLDER.value:
            # Subpasta: {perfil}/{nome}.{ext}
            output_filename = f"{input_path.stem}{input_path.suffix}"
            output_dir = Path(output_folder) / profile_suffix
            
        else:  # PROFILE_SUFFIX (default)
            # Sufixo: {nome}_{perfil}.{ext}
            output_filename = f"{input_path.stem}_{profile_suffix}{input_path.suffix}"
            output_dir = Path(output_folder)
        
        # Preservar estrutura de diretórios se opção estiver habilitada
        if options.get('preserve_structure', True) and input_path.parent != input_path.parent.anchor:
            try:
                # Tentar preservar estrutura relativa
                rel_path = input_path.parent.relative_to(input_path.parent.anchor)
                if str(rel_path) != '.':
                    output_dir = output_dir / rel_path
            except ValueError:
                pass
        
        # Criar diretório de output
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return str(output_dir / output_filename)
    
    def _get_profile_suffix(self, profile: Dict[str, Any]) -> str:
        """
        Gera sufixo único baseado no perfil.
        
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
    
    def _estimate_output_size(self, input_file: str, profile: Dict[str, Any]) -> int:
        """
        Estima tamanho do output baseado no perfil.
        
        Args:
            input_file: Caminho do arquivo de entrada
            profile: Perfil de codificação
            
        Returns:
            Tamanho estimado em bytes
        """
        input_size = self._get_file_size(input_file)
        
        if input_size == 0:
            return 0
        
        # Se perfil usa bitrate, calcular baseado na duração
        if profile.get('bitrate'):
            bitrate = self._parse_bitrate(profile['bitrate'])
            # Obter duração aproximada (simplificado - assume 1 hora como fallback)
            duration = self._get_video_duration(input_file) or 3600
            return int(bitrate * duration / 8)  # bits → bytes
        
        # Se perfil usa CQ, usar fator de compressão
        elif profile.get('cq'):
            cq = int(profile['cq'])
            # CQ menor = maior qualidade = maior arquivo
            # Faixa típica: CQ 18-28 para qualidade boa
            # Fator de compressão: 0.1 (CQ 18) a 0.5 (CQ 28)
            compression_factor = 0.1 + ((cq - 18) / 10) * 0.4
            compression_factor = max(0.05, min(0.8, compression_factor))
            return int(input_size * compression_factor)
        
        # Fallback: estimativa conservadora (30% do original)
        return int(input_size * 0.3)
    
    def _get_file_size(self, file_path: str) -> int:
        """Obtém tamanho do arquivo em bytes."""
        try:
            return Path(file_path).stat().st_size
        except (FileNotFoundError, OSError):
            return 0
    
    def _parse_bitrate(self, bitrate_str: str) -> int:
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
    
    def _get_video_duration(self, file_path: str) -> Optional[float]:
        """
        Obtém duração do vídeo em segundos.
        
        Nota: Esta é uma implementação simplificada.
        Para produção, usar FFmpeg para obter duração real.
        """
        # TODO: Implementar usando FFmpegWrapper.get_duration()
        # Por enquanto, retorna None para usar fallback
        return None
