#!/usr/bin/env python3
"""Script de teste para a nova funcionalidade de 'Salvar como Novo Perfil'."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.menu import Menu
from src.managers.profile_manager import ProfileManager

def test_save_as_new_profile():
    """Testa a funcionalidade de salvar como novo perfil."""
    print("Testando a nova funcionalidade: Salvar como Novo Perfil")
    
    # Criar instâncias necessárias
    menu = Menu()
    profile_mgr = ProfileManager()
    
    # Carregar um perfil existente para edição
    profiles = profile_mgr.list_profiles()
    if not profiles:
        print("Nenhum perfil encontrado para teste")
        return
    
    original_profile = profiles[0]  # Pegar o primeiro perfil
    print(f"Perfil original: {original_profile['name']}")
    
    # Simular edição do perfil
    edited_profile = original_profile.copy()
    edited_profile['name'] = f"{original_profile['name']} (editado)"
    edited_profile['cq'] = '20'  # Alterar algum valor para simular edição
    
    print(f"Perfil após edição: {edited_profile['name']}, CQ: {edited_profile.get('cq')}")
    
    # Testar a nova funcionalidade de salvar como novo perfil
    try:
        new_profile_id = profile_mgr.create_profile(
            name=f"{edited_profile['name']} (cópia)",
            codec=edited_profile.get('codec', 'hevc_nvenc'),
            cq=edited_profile.get('cq'),
            bitrate=edited_profile.get('bitrate'),
            preset=edited_profile.get('preset', 'p5'),
            resolution=edited_profile.get('resolution'),
            two_pass=edited_profile.get('two_pass', False),
            hdr_to_sdr=edited_profile.get('hdr_to_sdr', False),
            deinterlace=edited_profile.get('deinterlace', False),
            plex_compatible=edited_profile.get('plex_compatible', True),
            description=edited_profile.get('description', f'Cópia de {edited_profile["name"]}')
        )
        
        if new_profile_id:
            print(f"[SUCCESS] Novo perfil criado com sucesso: {new_profile_id}")
            
            # Verificar se o novo perfil foi salvo
            new_profile = profile_mgr.get_profile(new_profile_id)
            if new_profile:
                print(f"[SUCCESS] Novo perfil encontrado: {new_profile['name']}")
                print(f"  Codec: {new_profile['codec']}")
                print(f"  CQ: {new_profile.get('cq')}")
                print(f"  Descricao: {new_profile.get('description')}")
            else:
                print("[ERROR] Erro: Novo perfil nao encontrado apos criacao")
        else:
            print("[ERROR] Erro: Falha ao criar novo perfil")
    
    except Exception as e:
        print(f"[ERROR] Erro durante a criacao do novo perfil: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_as_new_profile()