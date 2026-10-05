"""
main.py — Ponto de entrada do sistema de controle de estoque.

Responsabilidades:
- Inicializar o banco de dados (criar tabelas se não existirem)
- Iniciar o menu interativo
- Tratar encerramentos abruptos (Ctrl+C) de forma limpa
"""

import sys
from db import criar_tabelas
from terminal import menu_principal


def main():
    """Função principal de inicialização da aplicação."""
    criar_tabelas()
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print("\n\nSistema encerrado pelo usuario. Ate logo!")
        sys.exit(0)


if __name__ == "__main__":
    main()
