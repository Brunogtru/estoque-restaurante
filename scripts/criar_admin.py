"""Cria o primeiro administrador sem exibir a senha digitada."""

from getpass import getpass

from db import SessionLocal, criar_tabelas
from erros import EstoqueError
from models import PapelUsuario
from services import cadastrar_usuario, existe_administrador_ativo


def main() -> None:
    criar_tabelas()

    with SessionLocal() as session:
        if existe_administrador_ativo(session):
            print("Ja existe um administrador ativo; este script cria apenas o administrador inicial.")
            print("Para cadastrar outros usuarios, use POST /usuarios pela API em /docs.")
            return

    nome = input("Nome do administrador: ").strip()
    login = input("Login do administrador: ").strip()
    senha = getpass("Senha: ")
    confirmacao = getpass("Confirme a senha: ")

    if senha != confirmacao:
        print("[ERRO] As senhas nao conferem. Nenhum usuario foi criado.")
        return

    try:
        with SessionLocal() as session:
            usuario = cadastrar_usuario(
                session=session,
                nome=nome,
                login=login,
                senha=senha,
                papel=PapelUsuario.ADMINISTRADOR,
            )
    except EstoqueError as erro:
        print(f"[ERRO] Nao foi possivel criar o administrador: {erro}")
        return

    print(f"[OK] Administrador '{usuario.login}' criado com sucesso (id={usuario.id}).")


if __name__ == "__main__":
    main()