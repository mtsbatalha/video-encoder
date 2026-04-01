#!/usr/bin/env python3
"""
Teste para validação das flags CUDA Acceleration no FFmpeg.
"""

import sys
import os

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

sys.path.insert(0, '.')

from src.core.ffmpeg_wrapper import FFmpegWrapper

# Strings de status compatíveis com Windows
PASSED = "[PASS]"
FAILED = "[FAIL]"


def test_cuda_accel_nvenc():
    """Testa se flags CUDA são adicionadas para codecs NVENC."""
    ffmpeg = FFmpegWrapper()
    
    # Teste para hevc_nvenc
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='hevc_nvenc',
        cq='18',
        preset='p5'
    )
    
    print("Teste 1: hevc_nvenc com cuda_accel=True (default)")
    print(f"Comando: {' '.join(command)}")
    
    assert '-hwaccel' in command, "Flag -hwaccel não encontrada"
    assert 'cuda' in command, "Flag cuda não encontrada"
    assert '-hwaccel_output_format' in command, "Flag -hwaccel_output_format não encontrada"
    print(f"{PASSED}: Flags CUDA presentes para hevc_nvenc\n")
    
    # Teste para h264_nvenc
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='h264_nvenc',
        cq='21',
        preset='p5'
    )
    
    print("Teste 2: h264_nvenc com cuda_accel=True (default)")
    print(f"Comando: {' '.join(command)}")
    
    assert '-hwaccel' in command, "Flag -hwaccel não encontrada"
    assert 'cuda' in command, "Flag cuda não encontrada"
    print(f"{PASSED}: Flags CUDA presentes para h264_nvenc\n")
    
    # Teste para av1_nvenc
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='av1_nvenc',
        cq='20',
        preset='p5'
    )
    
    print("Teste 3: av1_nvenc com cuda_accel=True (default)")
    print(f"Comando: {' '.join(command)}")
    
    assert '-hwaccel' in command, "Flag -hwaccel não encontrada"
    assert 'cuda' in command, "Flag cuda não encontrada"
    print(f"{PASSED}: Flags CUDA presentes para av1_nvenc\n")


def test_cuda_accel_disabled():
    """Testa se flags CUDA NÃO são adicionadas quando cuda_accel=False."""
    ffmpeg = FFmpegWrapper()
    
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='hevc_nvenc',
        cq='18',
        preset='p5',
        cuda_accel=False
    )
    
    print("Teste 4: hevc_nvenc com cuda_accel=False")
    print(f"Comando: {' '.join(command)}")
    
    assert '-hwaccel' not in command, "Flag -hwaccel encontrada mas deveria estar ausente"
    print(f"{PASSED}: Flags CUDA ausentes quando cuda_accel=False\n")


def test_cuda_accel_other_codecs():
    """Testa codecs não-NVIDIA (AMF, QSV, CPU)."""
    ffmpeg = FFmpegWrapper()
    
    # Teste para hevc_amf (AMD)
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='hevc_amf',
        cq='20',
        preset='balanced'
    )
    
    print("Teste 5: hevc_amf (AMD) - CUDA não deve ser adicionado")
    print(f"Comando: {' '.join(command)}")
    
    # Para codecs não-NVIDIA, as flags CUDA não devem ser adicionadas
    # (mesmo com cuda_accel=True, que é o default)
    assert '-hwaccel' not in command, "Flag -hwaccel encontrada para codec AMD"
    print(f"{PASSED}: Flags CUDA não adicionadas para codec AMD\n")
    
    # Teste para libx265 (CPU)
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='libx265',
        cq='22',
        preset='medium'
    )
    
    print("Teste 6: libx265 (CPU) - CUDA não deve ser adicionado")
    print(f"Comando: {' '.join(command)}")
    
    assert '-hwaccel' not in command, "Flag -hwaccel encontrada para codec CPU"
    print(f"{PASSED}: Flags CUDA não adicionadas para codec CPU\n")


def test_command_structure():
    """Testa a estrutura geral do comando com CUDA."""
    ffmpeg = FFmpegWrapper()
    
    command = ffmpeg.build_encoding_command(
        input_path="entrada.mkv",
        output_path="saida.mp4",
        codec='hevc_nvenc',
        cq='18',
        preset='p5'
    )
    
    print("Teste 7: Estrutura do comando com CUDA")
    print(f"Comando: {' '.join(command)}")
    
    # Verificar ordem: ffmpeg, -y, -stats, -hwaccel cuda, -hwaccel_output_format cuda, -i, ...
    assert command[0] == ffmpeg.ffmpeg, "Primeiro elemento deve ser o caminho do ffmpeg"
    assert command[1] == '-y', "Segundo elemento deve ser -y"
    assert command[2] == '-stats', "Terceiro elemento deve ser -stats"
    assert command[3] == '-hwaccel', "Quarto elemento deve ser -hwaccel"
    assert command[4] == 'cuda', "Quinto elemento deve ser 'cuda'"
    assert command[5] == '-hwaccel_output_format', "Sexto elemento deve ser -hwaccel_output_format"
    assert command[6] == 'cuda', "Sétimo elemento deve ser 'cuda'"
    assert command[7] == '-i', "Oitavo elemento deve ser -i"
    assert command[8] == 'entrada.mkv', "Nono elemento deve ser o input path"
    
    print(f"{PASSED}: Estrutura do comando está correta\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Testes de CUDA Acceleration para FFmpeg")
    print("=" * 60 + "\n")
    
    try:
        test_cuda_accel_nvenc()
        test_cuda_accel_disabled()
        test_cuda_accel_other_codecs()
        test_command_structure()
        
        print("=" * 60)
        print("[OK] TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"{FAILED} TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{FAILED} ERRO: {type(e).__name__}: {e}")
        sys.exit(1)
