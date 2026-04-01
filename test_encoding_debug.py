"""
Script de diagnóstico para investigar problema de progresso não sendo exibido.

Este script adiciona logs extensivos para rastrear:
1. Output raw do FFmpeg
2. Callbacks sendo chamados
3. Parsing de estatísticas
"""

import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.ffmpeg_wrapper import FFmpegWrapper
from src.ui.realtime_monitor import RealTimeEncodingMonitor, FFmpegProgressParser
import json
import time

def test_with_debug_logs():
    """Testa encoding com logs extensivos de debug."""
    
    # Arquivo de teste (ajuste para um arquivo real que você tem)
    # Usando um arquivo pequeno para teste rápido
    input_file = "/mnt/data/The.Devils.Advocate.1997.2160p.UNRATED.DC.UHD.Blu-ray.Remux.DV.HDR.HEVC.DTS-HD.MA.5.1-BTM.DUAL-Rick.SD.mkv"
    output_file = "/mnt/conversions2/TEST_DEBUG_OUTPUT.mkv"
    
    print("=" * 80)
    print("🔍 DIAGNÓSTICO: Iniciando teste de encoding com logs extensivos")
    print("=" * 80)
    
    # Verifica se arquivo existe
    if not os.path.exists(input_file):
        print(f"❌ ERRO: Arquivo de entrada não encontrado: {input_file}")
        print("\n⚠️  Ajuste a variável 'input_file' no script para um arquivo existente")
        return
    
    # Inicializa FFmpeg wrapper
    ffmpeg = FFmpegWrapper()
    
    # Obtém informações do arquivo
    print("\n📊 Obtendo informações do arquivo...")
    media_info = ffmpeg.get_media_info(input_file)
    
    if not media_info:
        print("❌ ERRO: Não foi possível obter informações do arquivo")
        return
    
    duration = float(media_info.get('format', {}).get('duration', 0))
    print(f"✅ Duração: {duration:.2f} segundos")
    
    # Inicializa monitor em tempo real
    print("\n🖥️  Inicializando monitor em tempo real...")
    monitor = RealTimeEncodingMonitor()
    
    # Ativa debug
    monitor.toggle_debug()
    print("✅ Debug ativado no monitor")
    
    # Inicializa parser
    parser = FFmpegProgressParser(monitor=monitor)
    parser.set_duration(duration)
    print(f"✅ Parser configurado com duração: {duration:.2f}s")
    
    # Contador de linhas recebidas
    line_counter = {'total': 0, 'progress': 0, 'empty': 0}
    
    def debug_callback(line: str):
        """Callback com logging extensivo."""
        line_counter['total'] += 1
        
        if not line or line.strip() == '':
            line_counter['empty'] += 1
            return
        
        # 🔍 LOG 1: Mostra TODAS as linhas recebidas (primeiras 10 e depois a cada 50)
        if line_counter['total'] <= 10 or line_counter['total'] % 50 == 0:
            print(f"\n🔍 LOG [Linha #{line_counter['total']}]: {line[:200]}")
        
        # Verifica se tem indicadores de progresso
        has_progress_indicators = any(
            indicator in line.lower() 
            for indicator in ['fps=', 'speed=', 'time=', 'frame=', 'bitrate=']
        )
        
        if has_progress_indicators:
            line_counter['progress'] += 1
            print(f"✅ PROGRESS LINE #{line_counter['progress']}: {line[:150]}")
        
        # 🔍 LOG 2: Tenta fazer parse
        stats = parser.parse_line(line)
        
        # 🔍 LOG 3: Mostra resultado do parse
        if stats:
            print(f"📊 STATS EXTRAÍDOS: {stats}")
            
            # Atualiza monitor
            if 'fps' in stats:
                monitor.update_encoding_stats(fps=stats['fps'])
            if 'speed' in stats:
                monitor.update_encoding_stats(speed=stats['speed'])
            if 'bitrate' in stats:
                monitor.update_encoding_stats(bitrate=stats['bitrate'])
            if 'current_time' in stats:
                monitor.update_progress(
                    progress=stats.get('progress', 0),
                    current_time=stats['current_time']
                )
        elif has_progress_indicators:
            print(f"⚠️  LINHA COM INDICADORES MAS SEM STATS EXTRAÍDOS")
    
    # Inicia monitor
    monitor.start(
        description="Debug Test",
        total_duration=duration,
        input_file=input_file,
        output_file=output_file,
        input_media_info=media_info,
        profile={'codec': 'hevc_nvenc', 'cq': '20', 'preset': 'p5'}
    )
    
    # Constrói comando FFmpeg (teste rápido - apenas 10 segundos)
    print("\n⚙️  Construindo comando FFmpeg (teste de 10 segundos)...")
    cmd = ffmpeg.build_encode_command(
        input_path=input_file,
        output_path=output_file,
        codec='hevc_nvenc',
        preset='p5',
        cq='20',
        cuda_accel=True,  # Força CUDA
        duration_limit=10  # Apenas 10 segundos para teste rápido
    )
    
    print(f"\n🔍 COMANDO FFMPEG:\n{' '.join(cmd)}\n")
    
    # Executa encoding
    print("\n🎬 Iniciando encoding...")
    print("📊 Estatísticas de linhas serão mostradas abaixo:\n")
    
    start_time = time.time()
    
    try:
        success, message = ffmpeg.execute_encode(
            command=cmd,
            callback=debug_callback,
            timeout=120  # 2 minutos de timeout
        )
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 RESUMO DO DIAGNÓSTICO")
        print("=" * 80)
        print(f"✅ Sucesso: {success}")
        print(f"📝 Mensagem: {message}")
        print(f"⏱️  Tempo decorrido: {elapsed:.2f}s")
        print(f"📊 Total de linhas recebidas: {line_counter['total']}")
        print(f"📊 Linhas vazias: {line_counter['empty']}")
        print(f"📊 Linhas com indicadores de progresso: {line_counter['progress']}")
        print("=" * 80)
        
        if line_counter['progress'] == 0:
            print("\n❌ PROBLEMA IDENTIFICADO: Nenhuma linha com indicadores de progresso foi recebida!")
            print("   Possíveis causas:")
            print("   1. FFmpeg não está emitindo estatísticas (flag -stats pode estar faltando)")
            print("   2. Formato de output diferente quando usando CUDA")
            print("   3. Output está sendo bufferizado e não chegando em tempo real")
        elif line_counter['total'] == 0:
            print("\n❌ PROBLEMA CRÍTICO: Nenhuma linha foi recebida do FFmpeg!")
            print("   Possíveis causas:")
            print("   1. Processo FFmpeg não iniciou")
            print("   2. Stdout/stderr não estão sendo capturados")
            print("   3. Processo travou imediatamente")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        ffmpeg.terminate()
    finally:
        monitor.stop()
        
        # Limpa arquivo de teste se foi criado
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"\n🗑️  Arquivo de teste removido: {output_file}")
            except:
                pass

if __name__ == '__main__':
    test_with_debug_logs()
