"""Rotas de autenticação e sessão do usuário."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response, status
from itsdangerous import URLSafeSerializer
from sqlalchemy.orm import Session

from api.dependencias import get_current_user, get_db
from api.schemas import LoginCredenciais, UsuarioResposta
from config import COOKIE_SECURE, SECRET_KEY, SESSION_TTL_MINUTES
from erros import CredenciaisInvalidasError
from models import Sessao, Usuario
from services import autenticar_usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])

def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(SECRET_KEY, salt="session-cookie")


@router.post("/login", response_model=UsuarioResposta, status_code=status.HTTP_200_OK)
def login(
    dados: LoginCredenciais,
    response: Response,
    session: Session = Depends(get_db),
):
    """Autentica o usuário e cria uma sessão segura em cookie HttpOnly."""
    usuario = autenticar_usuario(session, dados.login, dados.senha)
    token_plano = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_plano.encode("utf-8")).hexdigest()
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=SESSION_TTL_MINUTES)

    sessao = Sessao(
        token_hash=token_hash,
        usuario_id=usuario.id,
        expira_em=expira_em,
    )
    session.add(sessao)
    session.commit()
    session.refresh(sessao)

    cookie_valor = _serializer().dumps(token_plano)
    response.set_cookie(
        key="session",
        value=cookie_valor,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_TTL_MINUTES * 60,
        path="/",
    )
    return usuario


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_db),
):
    """Revoga a sessão atual e remove o cookie do navegador."""
    valor_cookie = request.cookies.get("session")
    if valor_cookie:
        try:
            token_plano = _serializer().loads(valor_cookie)
            token_hash = hashlib.sha256(token_plano.encode("utf-8")).hexdigest()
            agora = datetime.now(timezone.utc)
            session.query(Sessao).filter(
                Sessao.token_hash == token_hash,
                Sessao.revogada_em.is_(None),
            ).update({Sessao.revogada_em: agora})
            session.commit()
        except Exception:
            pass

    response.delete_cookie(key="session", path="/")
    return {"mensagem": "logout realizado"}


@router.get("/me", response_model=UsuarioResposta)
def quem_sou_eu(
    usuario: Usuario = Depends(get_current_user),
):
    """Devolve o usuário autenticado a partir da sessão atual."""
    return usuario
