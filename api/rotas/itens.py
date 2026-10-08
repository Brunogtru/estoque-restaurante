"""
api/rotas/itens.py — Rotas HTTP para operações sobre itens do estoque.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencias import get_current_user, get_db
from api.schemas import (
    ItemCriar,
    ItemEditar,
    ItemResposta,
    ItemComSaldoResposta,
    ItemAlertaResposta,
    SaldoResposta,
    MovimentacaoResposta,
)
import services
from models import Usuario

router = APIRouter(prefix="/itens", tags=["Itens"])


@router.get("", response_model=list[ItemComSaldoResposta])
def listar_todos_os_itens(
    usuario_logado: Usuario = Depends(get_current_user),
    apenas_ativos: bool = True,
    session: Session = Depends(get_db),
):
    """
    Lista todos os itens cadastrados no sistema, incluindo o saldo atual de cada um.
    Use o parâmetro 'apenas_ativos=false' para ver também itens desativados.
    """
    itens = services.listar_itens(session, apenas_ativos=apenas_ativos)
    resultado = []
    for item in itens:
        saldo = services.calcular_saldo(session, item.id)
        resultado.append(
            ItemComSaldoResposta(
                id=item.id,
                nome=item.nome,
                unidade=item.unidade,
                estoque_minimo=item.estoque_minimo,
                ativo=item.ativo,
                saldo=saldo,
            )
        )
    return resultado


@router.post("", response_model=ItemResposta, status_code=status.HTTP_201_CREATED)
def cadastrar_item(
    dados: ItemCriar,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Cadastra um novo item no estoque.
    Valida nome não vazio, unidade (g, ml, un) e estoque mínimo >= 0 na camada de serviço.
    """
    return services.cadastrar_item(
        session=session,
        usuario_executor=usuario_executor,
        nome=dados.nome,
        unidade=dados.unidade,
        estoque_minimo=dados.estoque_minimo,
    )


@router.get("/abaixo-do-minimo", response_model=list[ItemAlertaResposta])
def relatorio_itens_abaixo_do_minimo(
    usuario_logado: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Retorna apenas itens ativos cujo saldo atual está abaixo do estoque mínimo.
    Calculado em consulta agregada única no banco de dados.
    """
    itens_alerta = services.listar_itens_abaixo_do_minimo(session)
    return [
        ItemAlertaResposta(
            item=ItemResposta.model_validate(item),
            saldo_atual=saldo,
            falta=item.estoque_minimo - saldo,
        )
        for item, saldo in itens_alerta
    ]


@router.get("/{item_id}", response_model=ItemComSaldoResposta)
def buscar_item_por_id(
    item_id: int,
    usuario_logado: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Busca um item pelo seu ID e retorna com seu saldo atual."""
    item = services.buscar_item_por_id(session, item_id)
    saldo = services.calcular_saldo(session, item.id)
    return ItemComSaldoResposta(
        id=item.id,
        nome=item.nome,
        unidade=item.unidade,
        estoque_minimo=item.estoque_minimo,
        ativo=item.ativo,
        saldo=saldo,
    )


@router.put("/{item_id}", response_model=ItemResposta)
def editar_item(
    item_id: int,
    dados: ItemEditar,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Edita dados cadastrais de um item existente.
    Bloqueia alteração se o item for inativo ou se tentar mudar a unidade com movimentações já existentes.
    """
    return services.editar_item(
        session=session,
        usuario_executor=usuario_executor,
        item_id=item_id,
        nome=dados.nome,
        unidade=dados.unidade,
        estoque_minimo=dados.estoque_minimo,
    )


@router.patch("/{item_id}/desativar", response_model=ItemResposta)
def desativar_item(
    item_id: int,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Desativa um item (soft delete), impedindo novas movimentações."""
    return services.desativar_item(session, usuario_executor, item_id)


@router.patch("/{item_id}/reativar", response_model=ItemResposta)
def reativar_item(
    item_id: int,
    usuario_executor: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Reativa um item previamente desativado."""
    return services.reativar_item(session, usuario_executor, item_id)


@router.get("/{item_id}/saldo", response_model=SaldoResposta)
def consultar_saldo_item(
    item_id: int,
    usuario_logado: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Retorna apenas o saldo numérico atual calculado para um item."""
    # Garante que o item existe antes de calcular saldo
    services.buscar_item_por_id(session, item_id)
    saldo = services.calcular_saldo(session, item_id)
    return SaldoResposta(item_id=item_id, saldo=saldo)


@router.get("/{item_id}/extrato", response_model=list[MovimentacaoResposta])
def consultar_extrato_item(
    item_id: int,
    usuario_logado: Usuario = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Retorna o histórico cronológico completo de movimentações de um item."""
    return services.listar_movimentacoes(session, item_id)
