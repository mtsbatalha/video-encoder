#!/usr/bin/env python3
"""
Fabrica de Conversão NVENC Pro v2.0
Codificação de vídeo acelerada por GPU (NVIDIA, AMD, Intel, CPU).

Ponto de entrada principal do aplicativo.
"""

import sys
from src.cli import main


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro fatal: {e}", file=sys.stderr)
        sys.exit(1)
