"""
api/rotas/movimentacoes.py — Rotas HTTP para registro de movimentações de estoque.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencias import get_db
from api.schemas import MovimentacaoCriar, MovimentacaoResposta
import services

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])


@router.post("", response_model=MovimentacaoResposta, status_code=status.HTTP_201_CREATED)
def registrar_movimentacao(
    dados: MovimentacaoCriar,
    session: Session = Depends(get_db),
):
    """
    Registra uma movimentação de estoque (ENTRADA ou SAIDA).

    Validações aplicadas em services.py:
    1. Quantidade > 0
    2. Compatibilidade estrita entre tipo e motivo (ENTRADA: COMPRA; SAIDA: USO/PERDA/VENCIMENTO)
    3. Item deve existir
    4. Item deve estar ativo
    5. Se for SAIDA, saldo atual deve ser suficiente
    """
    return services.registrar_movimentacao(
        session=session,
        item_id=dados.item_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        motivo=dados.motivo,
    )
