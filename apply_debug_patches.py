"""
Script para aplicar patches temporários de debug no código.

Este script adiciona logs extensivos em pontos críticos para diagnosticar
o problema de progresso não sendo exibido.

IMPORTANTE: Execute este script ANTES de rodar a conversão problemática.
           Execute 'revert_debug_patches.py' DEPOIS para remover os logs.
"""

import os
import shutil
from datetime import datetime

# Arquivos que serão modificados
FILES_TO_PATCH = [
    'src/core/ffmpeg_wrapper.py',
    'src/ui/realtime_monitor.py',
    'src/core/encoder_engine.py'
]

def backup_files():
    """Cria backup dos arquivos originais."""
    backup_dir = f".debug_backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in FILES_TO_PATCH:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, file_path.replace('/', '_'))
            shutil.copy2(file_path, backup_path)
            print(f"[BACKUP] {file_path} -> {backup_path}")
    
    return backup_dir

def patch_ffmpeg_wrapper():
    """Adiciona logs no ffmpeg_wrapper.py."""
    file_path = 'src/core/ffmpeg_wrapper.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patch 1: Adiciona log quando linha é recebida do FFmpeg
    old_code_1 = '''                            for line in lines:
                                line = line.strip()
                                if line:
                                    output_lines.append(line)
                                    if callback:'''
    
    new_code_1 = '''                            for line in lines:
                                line = line.strip()
                                if line:
                                    output_lines.append(line)
                                    # [DEBUG PATCH] Log TODAS as linhas recebidas
                                    if not hasattr(callback, '_debug_line_count'):
                                        callback._debug_line_count = 0
                                    callback._debug_line_count += 1
                                    if callback._debug_line_count <= 5 or callback._debug_line_count % 20 == 0:
                                        print(f"\\n[FFMPEG LINE #{callback._debug_line_count}] {line[:150]}")
                                    if callback:'''
    
    if old_code_1 in content:
        content = content.replace(old_code_1, new_code_1)
        print("[PATCH 1] Log de linhas recebidas do FFmpeg - APLICADO")
    else:
        print("[AVISO] Patch 1 não aplicado: código não encontrado")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def patch_realtime_monitor():
    """Adiciona logs no realtime_monitor.py."""
    file_path = 'src/ui/realtime_monitor.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patch: Força debug mode sempre ativo
    old_code = '''        # Controle de debug
        self._debug_enabled: bool = False'''
    
    new_code = '''        # Controle de debug
        self._debug_enabled: bool = True  # [DEBUG PATCH] Forçar debug ativo'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("[PATCH 2] Debug forçado ativo no monitor - APLICADO")
    else:
        print("[AVISO] Patch 2 não aplicado: código não encontrado")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def patch_encoder_engine():
    """Adiciona logs no encoder_engine.py."""
    file_path = 'src/core/encoder_engine.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patch: Adiciona log no callback de progresso
    old_code = '''        def progress_callback(output: str):
            stats = parser.parse_line(output)
            
            if 'fps' in stats:
                self.realtime_monitor.update_encoding_stats(fps=stats['fps'])
            if 'speed' in stats:
                self.realtime_monitor.update_encoding_stats(speed=stats['speed'])
            if 'bitrate' in stats:
                self.realtime_monitor.update_encoding_stats(bitrate=stats['bitrate'])
            if 'current_time' in stats:
                self.realtime_monitor.update_progress(
                    progress=stats.get('progress', 0),
                    current_time=stats['current_time']
                )'''
    
    new_code = '''        def progress_callback(output: str):
            # [DEBUG PATCH] Log callback sendo chamado
            if not hasattr(progress_callback, '_call_count'):
                progress_callback._call_count = 0
            progress_callback._call_count += 1
            if progress_callback._call_count <= 3 or progress_callback._call_count % 10 == 0:
                print(f"\\n[CALLBACK #{progress_callback._call_count}] {output[:100]}")
            
            stats = parser.parse_line(output)
            
            # [DEBUG PATCH] Log stats extraídos
            if stats and (progress_callback._call_count <= 3 or progress_callback._call_count % 10 == 0):
                print(f"[STATS] {stats}")
            
            if 'fps' in stats:
                self.realtime_monitor.update_encoding_stats(fps=stats['fps'])
            if 'speed' in stats:
                self.realtime_monitor.update_encoding_stats(speed=stats['speed'])
            if 'bitrate' in stats:
                self.realtime_monitor.update_encoding_stats(bitrate=stats['bitrate'])
            if 'current_time' in stats:
                self.realtime_monitor.update_progress(
                    progress=stats.get('progress', 0),
                    current_time=stats['current_time']
                )'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("[PATCH 3] Log no callback de progresso - APLICADO")
    else:
        print("[AVISO] Patch 3 não aplicado: código não encontrado")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Aplica todos os patches."""
    print("=" * 80)
    print("APLICANDO PATCHES DE DEBUG")
    print("=" * 80)
    
    # Cria backups
    print("\nCriando backups...")
    backup_dir = backup_files()
    print(f"[OK] Backups salvos em: {backup_dir}")
    
    # Aplica patches
    print("\nAplicando patches...")
    patch_ffmpeg_wrapper()
    patch_realtime_monitor()
    patch_encoder_engine()
    
    print("\n" + "=" * 80)
    print("PATCHES APLICADOS COM SUCESSO!")
    print("=" * 80)
    print("\nPróximos passos:")
    print("1. Execute sua conversão normalmente")
    print("2. Observe os logs de debug no console")
    print("3. Execute 'python revert_debug_patches.py' para remover os patches")
    print(f"4. Os backups estão em: {backup_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
