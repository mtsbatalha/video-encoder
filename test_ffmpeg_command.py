#!/usr/bin/env python3
"""
Script para testar a construção do comando FFmpeg.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.ffmpeg_wrapper import FFmpegWrapper


def test_ffmpeg_command():
    """Testa a construção do comando FFmpeg."""
    print("=== Teste: Construção do Comando FFmpeg ===\n")
    
    ffmpeg = FFmpegWrapper()
    
    # Verificar se FFmpeg está instalado
    if not ffmpeg.verify_installation():
        print("[ERRO] FFmpeg não está instalado ou não está no PATH")
        return
    
    print("FFmpeg está instalado\n")
    
    # Testar com um arquivo de exemplo (mesmo que não exista, para ver o comando)
    input_path = "/mnt/data/test_video.mkv"
    output_path = "/mnt/conversions/test_video_out.mkv"
    
    profile = {
        "name": "NVENC - Tempo Real",
        "codec": "hevc_nvenc",
        "cq": 20,
        "preset": "p5",
        "two_pass": False,
        "hdr_to_sdr": False,
        "deinterlace": False,
        "audio_tracks": None,
        "subtitle_burn": False,
        "plex_compatible": True,
        "conversion_speed": None,
        "hardware_category": None
    }
    
    # Construir comando
    command = ffmpeg.build_encoding_command(
        input_path=input_path,
        output_path=output_path,
        codec=profile["codec"],
        cq=profile["cq"],
        bitrate=profile.get("bitrate"),
        resolution=profile.get("resolution"),
        preset=profile["preset"],
        two_pass=profile["two_pass"],
        hdr_to_sdr=profile["hdr_to_sdr"],
        deinterlace=profile["deinterlace"],
        audio_tracks=profile["audio_tracks"],
        subtitle_burn=profile["subtitle_burn"],
        plex_compatible=profile["plex_compatible"],
        conversion_speed=profile.get("conversion_speed"),
        hardware_category=profile.get("hardware_category")
    )
    
    print("Comando FFmpeg construído:")
    print(" ".join(command))
    print()
    
    # Testar obtenção de informações de mídia (se arquivo existir)
    print("Testando get_media_info (pode falhar se arquivo não existir):")
    try:
        media_info = ffmpeg.get_media_info(input_path)
        print(f"  Streams de vídeo: {len(ffmpeg.get_video_streams(media_info))}")
        print(f"  Streams de áudio: {len(ffmpeg.get_audio_streams(media_info))}")
    except Exception as e:
        print(f"  Erro (esperado se arquivo não existir): {e}")
    
    print("\n=== Fim do Teste ===")


if __name__ == "__main__":
    test_ffmpeg_command()
