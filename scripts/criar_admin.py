"""Cria o primeiro administrador sem exibir a senha digitada."""

from getpass import getpass

from db import SessionLocal, criar_tabelas
from erros import EstoqueError
from services import criar_primeiro_administrador


def main() -> None:
    criar_tabelas()

    nome = input("Nome do administrador: ").strip()
    login = input("Login do administrador: ").strip()
    senha = getpass("Senha: ")
    confirmacao = getpass("Confirme a senha: ")

    if senha != confirmacao:
        print("[ERRO] As senhas nao conferem. Nenhum usuario foi criado.")
        return

    try:
        with SessionLocal() as session:
            usuario = criar_primeiro_administrador(
                session=session,
                nome=nome,
                login=login,
                senha=senha,
            )
    except EstoqueError as erro:
        print(f"[ERRO] Nao foi possivel criar o administrador: {erro}")
        return

    print(f"[OK] Administrador '{usuario.login}' criado com sucesso (id={usuario.id}).")


if __name__ == "__main__":
    main()