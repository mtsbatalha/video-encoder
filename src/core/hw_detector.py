"""
Hardware Detector - Detecção de hardware para encoding de vídeo.

Detecta GPUs NVIDIA (NVENC), AMD (AMF), Intel iGPU (QSV) e informações de CPU.
"""

import subprocess
import json
import shutil
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class HardwareBackend(Enum):
    """Backends de encoding suportados."""
    NVIDIA_NVENC = "nvenc"
    AMD_AMF = "amf"
    INTEL_QSV = "qsv"
    CPU = "cpu"


@dataclass
class HardwareCapabilities:
    """Capacidades de hardware detectadas."""
    gpus_nvidia: List[Dict[str, Any]] = field(default_factory=list)
    gpus_amd: List[Dict[str, Any]] = field(default_factory=list)
    igpu_intel: Optional[Dict[str, Any]] = None
    igpu_amd: Optional[Dict[str, Any]] = None
    cpu_cores: int = 0
    cpu_threads: int = 0
    cpu_name: str = ""
    ram_gb: float = 0.0
    recommended_backend: str = "cpu"
    available_codecs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "gpus_nvidia": self.gpus_nvidia,
            "gpus_amd": self.gpus_amd,
            "igpu_intel": self.igpu_intel,
            "igpu_amd": self.igpu_amd,
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "cpu_name": self.cpu_name,
            "ram_gb": self.ram_gb,
            "recommended_backend": self.recommended_backend,
            "available_codecs": self.available_codecs
        }
    
    def get_recommended_profiles(self) -> List[str]:
        """Retorna IDs de perfis recomendados baseados no hardware."""
        profiles = []
        
        # Prioridade: NVIDIA > AMD GPU > Intel iGPU > AMD iGPU > CPU
        if self.gpus_nvidia:
            profiles.extend([
                "nvidia_filmes_1080p_hevc",
                "nvidia_filmes_1080p_h264",
                "nvidia_series_1080p_hevc",
                "nvidia_series_1080p_h264",
                "nvidia_filmes_4k_hevc",
                "nvidia_series_4k_hevc"
            ])
        elif self.gpus_amd:
            profiles.extend([
                "amd_gpu_filmes_1080p_hevc",
                "amd_gpu_filmes_1080p_h264",
                "amd_gpu_series_1080p_hevc",
                "amd_gpu_series_1080p_h264"
            ])
        elif self.igpu_intel:
            profiles.extend([
                "intel_igpu_filmes_1080p_hevc",
                "intel_igpu_filmes_1080p_h264",
                "intel_igpu_series_1080p_hevc",
                "intel_igpu_series_1080p_h264"
            ])
        elif self.igpu_amd:
            profiles.extend([
                "amd_igpu_filmes_1080p_hevc",
                "amd_igpu_filmes_1080p_h264",
                "amd_igpu_series_1080p_hevc",
                "amd_igpu_series_1080p_h264"
            ])
        else:
            profiles.extend([
                "cpu_rapido_filmes_1080p_hevc",
                "cpu_rapido_filmes_1080p_h264",
                "cpu_rapido_series_1080p_hevc",
                "cpu_rapido_series_1080p_h264"
            ])
        
        return profiles


class HardwareDetector:
    """Detector de hardware de encoding."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg = ffmpeg_path or shutil.which('ffmpeg') or 'ffmpeg'
        self._capabilities: Optional[HardwareCapabilities] = None
    
    def detect(self) -> HardwareCapabilities:
        """Detecta hardware disponível e retorna capacidades."""
        caps = HardwareCapabilities()
        
        # Detectar CPUs e RAM
        caps.cpu_cores, caps.cpu_threads = self._get_cpu_info()
        caps.ram_gb = self._get_ram_info()
        
        # Detectar GPUs
        caps.gpus_nvidia = self._detect_nvidia_gpu()
        caps.gpus_amd = self._detect_amd_gpu()
        caps.igpu_intel = self._detect_intel_igpu()
        caps.igpu_amd = self._detect_amd_igpu()
        
        # Detectar codecs disponíveis no FFmpeg
        caps.available_codecs = self._get_available_codecs()
        
        # Determinar backend recomendado
        caps.recommended_backend = self._get_recommended_backend(caps)
        
        self._capabilities = caps
        return caps
    
    def _get_cpu_info(self) -> tuple[int, int]:
        """Obtém informações da CPU."""
        try:
            import psutil
            cores = psutil.cpu_count(logical=False) or 0
            threads = psutil.cpu_count(logical=True) or 0
            return (cores, threads)
        except ImportError:
            import os
            cores = os.cpu_count() or 0
            return (cores, cores * 2)
    
    def _get_ram_info(self) -> float:
        """Obtém quantidade de RAM em GB."""
        try:
            import psutil
            ram_bytes = psutil.virtual_memory().total
            return round(ram_bytes / (1024 ** 3), 2)
        except ImportError:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong
                
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', c_ulonglong),
                        ('ullAvailPhys', c_ulonglong),
                        ('ullTotalPageFile', c_ulonglong),
                        ('ullAvailPageFile', c_ulonglong),
                        ('ullTotalVirtual', c_ulonglong),
                        ('ullAvailVirtual', c_ulonglong),
                        ('ullAvailExtendedVirtual', c_ulonglong),
                    ]
                
                memoryStatus = MEMORYSTATUSEX()
                memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
                return round(memoryStatus.ullTotalPhys / (1024 ** 3), 2)
            except Exception:
                return 0.0
    
    def _detect_nvidia_gpu(self) -> List[Dict[str, Any]]:
        """Detecta GPUs NVIDIA usando pynvml ou métodos alternativos."""
        gpus = []
        
        try:
            import pynvml
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')
                    
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_gb = round(memory_info.total / (1024 ** 3), 2)
                    nvenc_supported = self._check_codec_available('hevc_nvenc')
                    
                    gpus.append({
                        "index": i,
                        "name": name,
                        "memory_gb": memory_gb,
                        "nvenc_supported": nvenc_supported,
                        "driver_version": pynvml.nvmlSystemGetDriverVersion()
                    })
                
                pynvml.nvmlShutdown()
            except pynvml.NVMLError:
                pass
        except ImportError:
            # pynvml não instalado - tenta métodos alternativos
            try:
                import subprocess
                # Tenta obter informações via nvidia-smi
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for i, line in enumerate(lines):
                        parts = line.split(', ')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            memory_gb = float(parts[1].strip())
                            nvenc_supported = self._check_codec_available('hevc_nvenc')
                            
                            gpus.append({
                                "index": i,
                                "name": name,
                                "memory_gb": memory_gb,
                                "nvenc_supported": nvenc_supported
                            })
            except FileNotFoundError:
                # nvidia-smi não encontrado, tenta verificar se temos codecs NVENC disponíveis
                if self._check_codec_available('hevc_nvenc'):
                    gpus.append({
                        "name": "NVIDIA GPU (detectada via FFmpeg)",
                        "memory_gb": 0,
                        "nvenc_supported": True
                    })
            except Exception:
                # Se tudo falhar mas codec estiver disponível, registra GPU genérica
                if self._check_codec_available('hevc_nvenc'):
                    gpus.append({
                        "name": "NVIDIA GPU (detectada via FFmpeg)",
                        "memory_gb": 0,
                        "nvenc_supported": True
                    })
        
        return gpus
    
    def _detect_amd_gpu(self) -> List[Dict[str, Any]]:
        """Detecta GPUs AMD discretas."""
        gpus = []
        
        try:
            import win32com.client
            wmi = win32com.client.GetObject("winmgmts:")
            gpu_list = wmi.InstancesOf("Win32_VideoController")
            
            for gpu in gpu_list:
                name = gpu.Name
                if 'AMD' in name.upper() or 'RADEON' in name.upper():
                    if any(igpu in name.upper() for igpu in ['VEGA', 'RADEON GRAPHICS', 'AMD GRAPHICS']):
                        continue
                    
                    amf_supported = self._check_codec_available('hevc_amf')
                    gpus.append({
                        "name": name,
                        "vram_gb": 0,
                        "amf_supported": amf_supported
                    })
        except Exception:
            pass
        
        if not gpus and self._check_codec_available('hevc_amf'):
            gpus.append({
                "name": "AMD GPU (detectada via FFmpeg)",
                "vram_gb": 0,
                "amf_supported": True
            })
        
        return gpus
    
    def _detect_intel_igpu(self) -> Optional[Dict[str, Any]]:
        """Detecta iGPU Intel."""
        igpu = None
        
        try:
            import win32com.client
            wmi = win32com.client.GetObject("winmgmts:")
            gpu_list = wmi.InstancesOf("Win32_VideoController")
            
            for gpu in gpu_list:
                name = gpu.Name
                if 'INTEL' in name.upper() and ('UHD' in name.upper() or 'HD GRAPHICS' in name.upper() or 'IRIS' in name.upper()):
                    qsv_supported = self._check_codec_available('hevc_qsv')
                    igpu = {
                        "name": name,
                        "qsv_supported": qsv_supported,
                        "type": "Intel iGPU"
                    }
                    break
        except Exception:
            pass
        
        if not igpu and self._check_codec_available('hevc_qsv'):
            igpu = {
                "name": "Intel iGPU (detectada via FFmpeg)",
                "qsv_supported": True,
                "type": "Intel iGPU"
            }
        
        return igpu
    
    def _detect_amd_igpu(self) -> Optional[Dict[str, Any]]:
        """Detecta iGPU AMD (Radeon Vega, Radeon Graphics, etc.)."""
        igpu = None
        
        try:
            import win32com.client
            wmi = win32com.client.GetObject("winmgmts:")
            gpu_list = wmi.InstancesOf("Win32_VideoController")
            
            for gpu in gpu_list:
                name = gpu.Name
                igpu_indicators = ['VEGA', 'RADEON GRAPHICS', 'AMD GRAPHICS', 'RADEON 7']
                if any(indicator in name.upper() for indicator in igpu_indicators):
                    amf_supported = self._check_codec_available('hevc_amf')
                    igpu = {
                        "name": name,
                        "amf_supported": amf_supported,
                        "type": "AMD iGPU"
                    }
                    break
        except Exception:
            pass
        
        if not igpu and self._check_codec_available('hevc_amf'):
            amd_gpus = self._detect_amd_gpu()
            if not amd_gpus:
                igpu = {
                    "name": "AMD iGPU (detectada via FFmpeg)",
                    "amf_supported": True,
                    "type": "AMD iGPU"
                }
        
        return igpu
    
    def _get_available_codecs(self) -> List[str]:
        """Lista codecs de encoding disponíveis no FFmpeg."""
        codecs = []
        
        try:
            result = subprocess.run(
                [self.ffmpeg, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                for codec in ['nvenc', 'amf', 'qsv', 'libx264', 'libx265', 'libsvtav1']:
                    if codec in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            codec_name = parts[1]
                            if codec_name not in codecs:
                                codecs.append(codec_name)
        except Exception:
            pass
        
        return codecs
    
    def _check_codec_available(self, codec: str) -> bool:
        """Verifica se um codec específico está disponível."""
        try:
            result = subprocess.run(
                [self.ffmpeg, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return codec in result.stdout.lower()
        except Exception:
            return False
    
    def _get_recommended_backend(self, caps: HardwareCapabilities) -> str:
        """Determina backend recomendado baseado no hardware."""
        if caps.gpus_nvidia and any(g.get('nvenc_supported', False) for g in caps.gpus_nvidia):
            return HardwareBackend.NVIDIA_NVENC.value
        elif caps.gpus_amd and any(g.get('amf_supported', False) for g in caps.gpus_amd):
            return HardwareBackend.AMD_AMF.value
        elif caps.igpu_intel and caps.igpu_intel.get('qsv_supported', False):
            return HardwareBackend.INTEL_QSV.value
        elif caps.igpu_amd and caps.igpu_amd.get('amf_supported', False):
            return HardwareBackend.AMD_AMF.value
        else:
            return HardwareBackend.CPU.value
    
    def get_capabilities(self) -> Optional[HardwareCapabilities]:
        """Retorna capacidades detectadas (requer detect() primeiro)."""
        return self._capabilities
    
    def get_recommended_profiles(self) -> List[str]:
        """Retorna IDs de perfis recomendados para hardware detectado."""
        if self._capabilities:
            return self._capabilities.get_recommended_profiles()
        return []
    
    def list_available_codecs(self) -> List[str]:
        """Lista codecs disponíveis no sistema."""
        if self._capabilities:
            return self._capabilities.available_codecs
        return self._get_available_codecs()
    
    def get_hardware_summary(self) -> str:
        """Retorna resumo legível do hardware detectado."""
        if not self._capabilities:
            self.detect()
        
        caps = self._capabilities
        lines = []
        
        lines.append(f"CPU: {caps.cpu_name or 'N/A'} ({caps.cpu_cores} núcleos, {caps.cpu_threads} threads)")
        lines.append(f"RAM: {caps.ram_gb} GB")
        lines.append("")
        
        if caps.gpus_nvidia:
            for gpu in caps.gpus_nvidia:
                lines.append(f"GPU NVIDIA: {gpu['name']} ({gpu['memory_gb']} GB) - NVENC: {'Sim' if gpu.get('nvenc_supported') else 'Não'}")
        
        if caps.gpus_amd:
            for gpu in caps.gpus_amd:
                lines.append(f"GPU AMD: {gpu['name']} - AMF: {'Sim' if gpu.get('amf_supported') else 'Não'}")
        
        if caps.igpu_intel:
            lines.append(f"iGPU Intel: {caps.igpu_intel['name']} - QSV: {'Sim' if caps.igpu_intel.get('qsv_supported') else 'Não'}")
        
        if caps.igpu_amd:
            lines.append(f"iGPU AMD: {caps.igpu_amd['name']} - AMF: {'Sim' if caps.igpu_amd.get('amf_supported') else 'Não'}")
        
        lines.append("")
        lines.append(f"Backend recomendado: {caps.recommended_backend}")
        lines.append(f"Codecs disponíveis: {', '.join(caps.available_codecs) if caps.available_codecs else 'N/A'}")
        
        return '\n'.join(lines)
    
    def detect_all(self) -> Dict[str, Any]:
        """Detecta hardware e retorna formato legado para compatibilidade."""
        caps = self.detect()
        
        gpus = []
        
        for gpu in caps.gpus_nvidia:
            gpus.append({
                "name": gpu["name"],
                "vram_gb": gpu.get("memory_gb", 0),
                "category": "nvidia_gpu",
                "codec_support": ["hevc_nvenc", "h264_nvenc"] if gpu.get("nvenc_supported") else []
            })
        
        for gpu in caps.gpus_amd:
            gpus.append({
                "name": gpu["name"],
                "vram_gb": gpu.get("vram_gb", 0),
                "category": "amd_gpu",
                "codec_support": ["hevc_amf", "h264_amf"] if gpu.get("amf_supported") else []
            })
        
        return {
            "gpus": gpus,
            "cpu_available": caps.cpu_cores > 0,
            "nvidia_detected": len(caps.gpus_nvidia) > 0,
            "amd_gpu_detected": len(caps.gpus_amd) > 0,
            "intel_igpu_detected": caps.igpu_intel is not None,
            "amd_igpu_detected": caps.igpu_amd is not None,
            "codecs": caps.available_codecs
        }
    
    def get_available_codecs(self, ffmpeg_path: str) -> List[str]:
        """Lista codecs disponíveis usando caminho FFmpeg específico."""
        codecs = []
        
        try:
            result = subprocess.run(
                [ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                for codec in ['nvenc', 'amf', 'qsv', 'libx264', 'libx265', 'libsvtav1']:
                    if codec in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            codec_name = parts[1]
                            if codec_name not in codecs:
                                codecs.append(codec_name)
        except Exception:
            pass
        
        return codecs
