"""
api/rotas/movimentacoes.py — Rotas HTTP para registro de movimentações de estoque.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencias import get_current_user, get_db
from api.schemas import MovimentacaoCriar, MovimentacaoResposta
import services
from models import Usuario

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])


@router.post("", response_model=MovimentacaoResposta, status_code=status.HTTP_201_CREATED)
def registrar_movimentacao(
    dados: MovimentacaoCriar,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Registra uma movimentação de estoque (ENTRADA ou SAIDA).

    Validações aplicadas em services.py:
    1. Permissao do usuario autenticado
    2. Quantidade > 0
    3. Compatibilidade estrita entre tipo e motivo
    4. Item deve existir e estar ativo
    5. Se for SAIDA, saldo atual deve ser suficiente
    """
    return services.registrar_movimentacao(
        session=session,
        usuario_executor=usuario_executor,
        item_id=dados.item_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        motivo=dados.motivo,
    )
