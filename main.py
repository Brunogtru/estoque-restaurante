"""
main.py — Ponto de entrada do sistema de controle de estoque.

Pode ser executado de duas formas:
1. Terminal interativo (CLI):
   py main.py

2. Servidor web da API (FastAPI):
   py main.py --api
   (ou diretamente com: uvicorn api.app:app --reload)
"""

import sys
import uvicorn
from db import criar_tabelas
from terminal import menu_principal


def iniciar_terminal():
    """Inicia o menu de texto do terminal."""
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print("\n\nSistema encerrado pelo usuario. Ate logo!")
        sys.exit(0)


def iniciar_api():
    """Inicia o servidor HTTP da API."""
    print("Iniciando API em http://127.0.0.1:8000 ...")
    print("Documentacao interativa (Swagger): http://127.0.0.1:8000/docs")
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)


def main():
    criar_tabelas()
    if "--api" in sys.argv:
        iniciar_api()
    else:
        iniciar_terminal()


if __name__ == "__main__":
    main()
