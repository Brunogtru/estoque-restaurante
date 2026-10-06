"""Ponto de entrada da API do sistema de controle de estoque."""

import uvicorn


def iniciar_api():
    """Inicia o servidor HTTP da API."""
    print("Iniciando API em http://127.0.0.1:8000 ...")
    print("Documentacao interativa (Swagger): http://127.0.0.1:8000/docs")
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)


def main():
    iniciar_api()


if __name__ == "__main__":
    main()
