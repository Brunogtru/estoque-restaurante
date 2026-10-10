"""Rotas HTTP de usuários."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencias import get_current_user, get_db
from api.schemas import UsuarioCriar, UsuarioMudarPapel, UsuarioResposta
import services
from models import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(
    dados: UsuarioCriar,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Cadastra usuário delegando validações e persistência ao serviço."""
    return services.cadastrar_usuario(
        session=session,
        usuario_executor=usuario_executor,
        nome=dados.nome,
        login=dados.login,
        senha=dados.senha,
        papel=dados.papel,
    )


@router.get("", response_model=list[UsuarioResposta])
def listar_usuarios(
    usuario_executor: Usuario = Depends(get_current_user),
    apenas_ativos: bool = True,
    session: Session = Depends(get_db),
):
    """Lista usuários; por padrão, somente os ativos."""
    return services.listar_usuarios(
        session,
        usuario_executor,
        apenas_ativos=apenas_ativos,
    )


@router.get("/{usuario_id}", response_model=UsuarioResposta)
def buscar_usuario_por_id(
    usuario_id: int,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Busca usuário por ID."""
    return services.buscar_usuario_por_id(session, usuario_executor, usuario_id)


@router.patch("/{usuario_id}/papel", response_model=UsuarioResposta)
def mudar_papel_usuario(
    usuario_id: int,
    dados: UsuarioMudarPapel,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Altera o papel via serviço de domínio."""
    return services.mudar_papel_usuario(
        session,
        usuario_executor,
        usuario_id,
        dados.papel,
    )


@router.patch("/{usuario_id}/desativar", response_model=UsuarioResposta)
def desativar_usuario(
    usuario_id: int,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Desativa usuário via serviço de domínio."""
    return services.desativar_usuario(session, usuario_executor, usuario_id)


@router.patch("/{usuario_id}/reativar", response_model=UsuarioResposta)
def reativar_usuario(
    usuario_id: int,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Reativa usuário via serviço de domínio."""
    return services.reativar_usuario(session, usuario_executor, usuario_id)