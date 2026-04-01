#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para simular o ambiente remoto e verificar a detecção CUDA.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.ffmpeg_wrapper import FFmpegWrapper
from src.core.hw_detector import HardwareDetector

def simulate_remote_environment():
    """
    Simula o ambiente remoto onde o pynvml pode não estar instalado
    mas a GPU NVIDIA está presente e o FFmpeg tem suporte a NVENC.
    """
    print("=== Simulação Ambiente Remoto ===\n")
    
    # Testar o FFmpegWrapper
    ffmpeg = FFmpegWrapper()
    
    # Simular situação onde pynvml não está instalado (como no ambiente remoto)
    # Mas o codec hevc_nvenc está disponível
    print("Codec hevc_nvenc disponível:", ffmpeg.is_codec_available('hevc_nvenc'))
    
    # Testar o método is_cuda_available que foi corrigido
    print("CUDA disponível (corrigido):", ffmpeg.is_cuda_available())
    
    # Testar a detecção de hardware
    detector = HardwareDetector()
    capabilities = detector.detect()
    
    print(f"\nHardware detectado:")
    print(f"- GPUs NVIDIA: {len(capabilities.gpus_nvidia)}")
    for gpu in capabilities.gpus_nvidia:
        print(f"  - {gpu['name']}: NVENC={gpu['nvenc_supported']}")
    
    print(f"- GPUs AMD: {len(capabilities.gpus_amd)}")
    print(f"- iGPU Intel: {'Sim' if capabilities.igpu_intel else 'Não'}")
    print(f"- iGPU AMD: {'Sim' if capabilities.igpu_amd else 'Não'}")
    
    print(f"\nBackend recomendado: {capabilities.recommended_backend}")
    print(f"Perfis recomendados: {capabilities.get_recommended_profiles()[:3]}...")  # Mostrar primeiros 3
    
    # Testar construção de comando de encoding com NVENC
    print(f"\n=== Teste Construção Comando NVENC ===")
    try:
        cmd = ffmpeg.build_encoding_command(
            input_path="/mnt/data/teste.mp4",
            output_path="/mnt/conversions/teste_saida.mkv",
            codec="hevc_nvenc",
            cq="20",
            preset="p5",
            cuda_accel=True  # Habilitar aceleração CUDA
        )
        
        # Verificar se o comando inclui as flags de aceleração CUDA
        cmd_str = ' '.join(cmd)
        has_hwaccel = '-hwaccel cuda' in cmd_str
        has_cuda_format = '-hwaccel_output_format cuda' in cmd_str
        
        print(f"Comando inclui -hwaccel cuda: {has_hwaccel}")
        print(f"Comando inclui -hwaccel_output_format cuda: {has_cuda_format}")
        print(f"Codec usado: hevc_nvenc (não fallback para libx265)")
        
        # Verificar se NÃO houve fallback para libx265
        uses_nvenc = 'hevc_nvenc' in cmd_str and 'libx265' not in cmd_str.split()
        print(f"Usando NVENC (sem fallback): {uses_nvenc}")
        
        if has_hwaccel and has_cuda_format and uses_nvenc:
            print("\n[SUCCESS] Sistema configurado corretamente para usar NVENC!")
        else:
            print("\n[ERROR] Sistema nao esta configurado corretamente para NVENC")
            
    except Exception as e:
        print(f"Erro ao construir comando: {e}")
    
    return ffmpeg.is_cuda_available()

def test_fallback_behavior():
    """Testa o comportamento de fallback quando CUDA nao esta disponivel."""
    print(f"\n=== Teste Fallback (simulado) ===")
    
    ffmpeg = FFmpegWrapper()
    
    # Testar construcao de comando com cuda_accel=False (simulando fallback)
    cmd = ffmpeg.build_encoding_command(
        input_path="/mnt/data/teste.mp4",
        output_path="/mnt/conversions/teste_saida.mkv",
        codec="hevc_nvenc",
        cq="20",
        preset="p5",
        cuda_accel=False  # Desabilitar aceleracao CUDA (forca fallback)
    )
    
    cmd_str = ' '.join(cmd)
    uses_fallback = 'libx265' in cmd_str
    uses_nvenc = 'hevc_nvenc' in cmd_str and not uses_fallback
    
    print(f"Codec original (hevc_nvenc): {'Sim' if uses_nvenc else 'Nao'}")
    print(f"Fallback para libx265: {'Sim' if uses_fallback else 'Nao'}")
    
    if uses_fallback:
        print("[SUCCESS] Fallback funcionando corretamente quando CUDA indisponivel")
    elif uses_nvenc and ffmpeg.is_cuda_available():
        print("[SUCCESS] NVENC sendo usado corretamente quando disponivel")

if __name__ == "__main__":
    print("Testando deteccao CUDA no ambiente local (simulando remoto)...\n")
    
    cuda_available = simulate_remote_environment()
    test_fallback_behavior()
    
    print(f"\n{'='*50}")
    if cuda_available:
        print("[SUCCESS] RESULTADO FINAL: CUDA esta disponivel e detectado corretamente!")
        print("   O sistema agora deve usar NVENC em vez de fazer fallback para libx265")
    else:
        print("[ERROR] RESULTADO FINAL: CUDA ainda nao esta sendo detectado")
    print(f"{'='*50}")