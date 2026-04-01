"""
Script para reverter patches temporários de debug.

Este script restaura os arquivos originais a partir dos backups.
"""

import os
import shutil
import glob

def find_latest_backup():
    """Encontra o diretório de backup mais recente."""
    backup_dirs = glob.glob('.debug_backups_*')
    if not backup_dirs:
        return None
    return max(backup_dirs)

def restore_files(backup_dir):
    """Restaura arquivos do backup."""
    if not os.path.exists(backup_dir):
        print(f"❌ Diretório de backup não encontrado: {backup_dir}")
        return False
    
    # Lista todos os backups
    backup_files = os.listdir(backup_dir)
    
    restored_count = 0
    for backup_file in backup_files:
        # Converte nome do backup de volta para path original
        # Exemplo: src_core_ffmpeg_wrapper.py -> src/core/ffmpeg_wrapper.py
        original_path = backup_file.replace('_', '/', 2)
        backup_path = os.path.join(backup_dir, backup_file)
        
        if os.path.exists(backup_path):
            # Garante que diretório existe
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            
            # Restaura arquivo
            shutil.copy2(backup_path, original_path)
            print(f"✅ Restaurado: {original_path}")
            restored_count += 1
    
    return restored_count > 0

def main():
    """Reverte todos os patches."""
    print("=" * 80)
    print("🔄 REVERTENDO PATCHES DE DEBUG")
    print("=" * 80)
    
    # Encontra backup mais recente
    backup_dir = find_latest_backup()
    
    if not backup_dir:
        print("\n❌ Nenhum backup encontrado!")
        print("   Os arquivos não foram modificados ou os backups foram removidos.")
        return
    
    print(f"\n📦 Usando backup: {backup_dir}")
    
    # Restaura arquivos
    print("\n🔄 Restaurando arquivos...")
    if restore_files(backup_dir):
        print("\n" + "=" * 80)
        print("✅ PATCHES REVERTIDOS COM SUCESSO!")
        print("=" * 80)
        print(f"\n📝 O diretório de backup ainda existe: {backup_dir}")
        print("   Você pode removê-lo manualmente se quiser.")
    else:
        print("\n❌ Falha ao restaurar arquivos")

if __name__ == '__main__':
    main()
