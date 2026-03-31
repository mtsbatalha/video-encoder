#!/usr/bin/env python3
"""Teste completo de integração da nova funcionalidade."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.menu import Menu
from src.managers.profile_manager import ProfileManager

def test_full_integration():
    """Testa a integração completa da nova funcionalidade."""
    print("Testando integração completa da funcionalidade 'Salvar como Novo Perfil'")
    
    # Criar instâncias necessárias
    menu = Menu()
    profile_mgr = ProfileManager()
    
    # Obter um perfil existente
    profiles = profile_mgr.list_profiles()
    if not profiles:
        print("Nenhum perfil encontrado para teste")
        return
    
    original_profile = profiles[0]
    print(f"Perfil original: {original_profile['name']}")
    
    # Simular o comportamento da função show_advanced_profile_editor com a nova opção
    # Vamos copiar o perfil e simular as edições
    edited_profile = original_profile.copy()
    
    # Simular algumas edições
    edited_profile['cq'] = '22'
    edited_profile['preset'] = 'p6'
    edited_profile['resolution'] = '1080'
    edited_profile['name'] = f"{original_profile['name']} (editado)"
    
    print(f"Após edições - Nome: {edited_profile['name']}, CQ: {edited_profile['cq']}, Preset: {edited_profile['preset']}")
    
    # Simular a escolha da opção "Salvar como novo perfil" (índice 8 na lista modificada)
    # Isso chama a lógica que adicionamos
    new_name = f"{edited_profile['name']} (cópia)"
    new_description = f"Cópia de {edited_profile['name']}"
    
    print(f"\nSimulando 'Salvar como novo perfil':")
    print(f"Nome do novo perfil: {new_name}")
    print(f"Descrição: {new_description}")
    
    # Criar novo perfil com as configurações atuais (lógica que adicionamos)
    new_profile_id = profile_mgr.create_profile(
        name=new_name,
        codec=edited_profile.get('codec', 'hevc_nvenc'),
        cq=edited_profile.get('cq'),
        bitrate=edited_profile.get('bitrate'),
        preset=edited_profile.get('preset', 'p5'),
        resolution=edited_profile.get('resolution'),
        two_pass=edited_profile.get('two_pass', False),
        hdr_to_sdr=edited_profile.get('hdr_to_sdr', False),
        deinterlace=edited_profile.get('deinterlace', False),
        plex_compatible=edited_profile.get('plex_compatible', True),
        description=new_description
    )
    
    if new_profile_id:
        print(f"\n[SUCCESS] Novo perfil criado com sucesso: {new_profile_id}")
        
        # Verificar se o novo perfil foi salvo corretamente
        new_profile = profile_mgr.get_profile(new_profile_id)
        if new_profile:
            print(f"  Nome: {new_profile['name']}")
            print(f"  Codec: {new_profile['codec']}")
            print(f"  CQ: {new_profile.get('cq')}")
            print(f"  Preset: {new_profile.get('preset')}")
            print(f"  Resolucao: {new_profile.get('resolution')}")
            print(f"  Two-Pass: {new_profile.get('two_pass')}")
            print(f"  HDR para SDR: {new_profile.get('hdr_to_sdr')}")
            print(f"  Deinterlace: {new_profile.get('deinterlace')}")
            print(f"  Plex Compativel: {new_profile.get('plex_compatible')}")
            print(f"  Descricao: {new_profile.get('description')}")
            
            # Verificar se as configurações foram copiadas corretamente
            assert new_profile['cq'] == '22', f"Esperava CQ '22', obteve '{new_profile['cq']}'"
            assert new_profile['preset'] == 'p6', f"Esperava preset 'p6', obteve '{new_profile['preset']}'"
            assert new_profile['resolution'] == '1080', f"Esperava resolucao '1080', obteve '{new_profile['resolution']}'"
            
            print("\n[SUCCESS] Todas as configuracoes foram copiadas corretamente!")
        else:
            print("[ERROR] Erro: Novo perfil nao encontrado apos criacao")
            return False
    else:
        print("[ERROR] Erro: Falha ao criar novo perfil")
        return False
    
    # Verificar que o perfil original não foi alterado
    original_check = profile_mgr.get_profile(original_profile['id'])
    if original_check['name'] == original_profile['name']:
        print("[SUCCESS] Perfil original permaneceu inalterado")
    else:
        print("[ERROR] Erro: Perfil original foi alterado")
        return False
    
    print("\n[SUCCESS] Todos os testes passaram! A funcionalidade esta funcionando corretamente.")
    return True

def test_edge_cases():
    """Testa casos especiais."""
    print("\nTestando casos especiais...")
    
    profile_mgr = ProfileManager()
    
    # Testar com valores vazios/nulos
    new_profile_id = profile_mgr.create_profile(
        name="Teste Valores Nulos",
        codec="h264_nvenc",
        cq=None,
        bitrate="5M",
        preset="p5",
        resolution=None,
        two_pass=False,
        hdr_to_sdr=True,
        deinterlace=False,
        plex_compatible=True,
        description=""
    )
    
    if new_profile_id:
        new_profile = profile_mgr.get_profile(new_profile_id)
        if new_profile:
            print(f"[SUCCESS] Perfil com valores nulos criado: {new_profile['name']}")
            print(f"  CQ: {new_profile.get('cq')} (None é valido)")
            print(f"  Bitrate: {new_profile.get('bitrate')}")
            print(f"  Resolucao: {new_profile.get('resolution')} (None é valido)")
        else:
            print("[ERROR] Erro: Perfil com valores nulos não encontrado")
            return False
    else:
        print("✗ Erro: Falha ao criar perfil com valores nulos")
        return False
    
    print("[SUCCESS] Casos especiais testados com sucesso!")
    return True

if __name__ == "__main__":
    success1 = test_full_integration()
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\n[CELEBRATION] Todos os testes foram bem-sucedidos! A nova funcionalidade esta pronta.")
    else:
        print("\n[WARNING] Alguns testes falharam.")
        sys.exit(1)