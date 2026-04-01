#!/usr/bin/env python3
"""
Teste atualizado para verificar se CUDA está disponível após as correções.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.ffmpeg_wrapper import FFmpegWrapper
from src.core.hw_detector import HardwareDetector

def test_cuda_detection():
    print("=== Teste CUDA Availability (Atualizado) ===\n")

    # Testar o FFmpegWrapper
    ffmpeg = FFmpegWrapper()

    # Verificar se pynvml está disponível
    try:
        import pynvml
        print("pynvml está instalado")
        
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            print(f"  Número de GPUs NVIDIA detectadas: {device_count}")
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                print(f"  GPU {i}: {name}")
            
            pynvml.nvmlShutdown()
        except pynvml.NVMLError as e:
            print(f"  Erro ao inicializar pynvml: {e}")
            
    except ImportError:
        print("pynvml NÃO está instalado")

    # Verificar codecs disponíveis via ffmpeg
    print("\n=== Codecs FFmpeg ===")
    result = ffmpeg.get_all_video_codecs()
    print(f"Codecs disponíveis: {result}")

    # Verificar se hevc_nvenc está disponível
    print(f"\nhevc_nvenc disponível: {ffmpeg.is_codec_available('hevc_nvenc')}")

    # Testar nosso método is_cuda_available
    print(f"\n=== is_cuda_available() ===")
    cuda_available = ffmpeg.is_cuda_available()
    print(f"CUDA disponível: {cuda_available}")

    # Testar detecção de hardware
    print(f"\n=== Hardware Detection ===")
    detector = HardwareDetector()
    capabilities = detector.detect()
    
    print(f"NVIDIA GPUs detectadas: {len(capabilities.gpus_nvidia)}")
    for gpu in capabilities.gpus_nvidia:
        print(f"  - {gpu['name']} ({gpu['memory_gb']} GB) - NVENC: {gpu['nvenc_supported']}")
    
    print(f"AMD GPUs detectadas: {len(capabilities.gpus_amd)}")
    print(f"Intel iGPUs detectadas: {capabilities.igpu_intel is not None}")
    print(f"AMD iGPUs detectadas: {capabilities.igpu_amd is not None}")
    print(f"Backend recomendado: {capabilities.recommended_backend}")

    return cuda_available

if __name__ == "__main__":
    test_cuda_detection()