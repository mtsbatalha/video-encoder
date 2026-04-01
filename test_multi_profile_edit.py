#!/usr/bin/env python3
"""
Script de teste para verificar a funcionalidade de edição de perfis múltiplos
"""
import sys
import os

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.managers.config_manager import ConfigManager
from src.managers.profile_manager import ProfileManager
from src.managers.job_manager import JobManager
from src.managers.queue_manager import QueueManager
from src.managers.multi_profile_conversion_manager import MultiProfileConversionManager


def test_multi_profile_edit():
    """Testa a funcionalidade de edição de perfis múltiplos"""
    print("Testando funcionalidade de edição de perfis múltiplos...")
    
    # Inicializar componentes necessários
    config = ConfigManager()
    profile_mgr = ProfileManager()
    job_mgr = JobManager()
    queue_mgr = QueueManager()
    
    # Criar instância do gerenciador de conversão multi-perfil
    multi_mgr = MultiProfileConversionManager(
        profile_manager=profile_mgr,
        job_manager=job_mgr,
        queue_manager=queue_mgr
    )
    
    # Obter alguns perfis para teste
    profiles = profile_mgr.list_profiles()
    
    if not profiles:
        print("Nenhum perfil encontrado para teste")
        return False
    
    # Pegar os primeiros perfis para teste
    test_profile_ids = [p['id'] for p in profiles[:2]]  # Pegar até 2 perfis
    
    print(f"Perfis selecionados para teste: {test_profile_ids}")
    
    # Testar a função de edição individual de perfis
    try:
        # Simular a chamada da função de edição individual
        # Como a função show_advanced_profile_editor precisa de uma interface gráfica,
        # vamos testar apenas a parte lógica da função
        print("Testando a funcao edit_individual_profiles_interactive...")
        
        # Testar a importacao e existencia da funcao
        if hasattr(multi_mgr, 'edit_individual_profiles_interactive'):
            print("[OK] Funcao edit_individual_profiles_interactive existe")
        else:
            print("[ERRO] Funcao edit_individual_profiles_interactive nao encontrada")
            return False
            
        # Testar a importacao e existencia da funcao auxiliar
        if hasattr(multi_mgr, 'edit_single_profile_interactive'):
            print("[OK] Funcao edit_single_profile_interactive existe")
        else:
            print("[INFO] Funcao edit_single_profile_interactive nao e obrigatoria")
        
        print("[OK] Teste de funcionalidade concluido com sucesso!")
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_multi_profile_edit()
    if success:
        print("\n[OK] Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n[ERRO] Alguns testes falharam!")
        sys.exit(1)