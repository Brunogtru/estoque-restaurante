"""
api/dependencias.py — Injeção de dependências do FastAPI.

Fornece a sessão de banco de dados por requisição, garantindo
que a conexão seja fechada ao final do ciclo de vida HTTP.
"""

import hashlib
from datetime import datetime, timezone
from typing import Generator

from fastapi import Depends, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeSerializer
from sqlalchemy.orm import Session

from config import SECRET_KEY
from db import SessionLocal
from erros import CredenciaisInvalidasError
from models import Sessao, Usuario


def get_db() -> Generator[Session, None, None]:
    """
    Dependência que abre uma sessão com o banco para cada requisição HTTP
    e garante seu fechamento seguro no bloco finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    session: Session = Depends(get_db),
) -> Usuario:
    """Valida a sessão do cookie e devolve o usuário autenticado."""
    valor_cookie = request.cookies.get("session")
    if not valor_cookie:
        raise CredenciaisInvalidasError("Credenciais invalidas.")

    try:
        serializer = URLSafeSerializer(SECRET_KEY, salt="session-cookie")
        token_plano = serializer.loads(valor_cookie)
    except (BadSignature, SignatureExpired, ValueError):
        raise CredenciaisInvalidasError("Credenciais invalidas.") from None

    token_hash = hashlib.sha256(token_plano.encode("utf-8")).hexdigest()
    agora = datetime.now(timezone.utc)
    sessao = (
        session.query(Sessao)
        .filter(
            Sessao.token_hash == token_hash,
            Sessao.revogada_em.is_(None),
            Sessao.expira_em > agora,
        )
        .first()
    )

    if sessao is None:
        raise CredenciaisInvalidasError("Credenciais invalidas.")

    usuario = session.get(Usuario, sessao.usuario_id)
    if usuario is None or not usuario.ativo:
        raise CredenciaisInvalidasError("Credenciais invalidas.")

    return usuario
