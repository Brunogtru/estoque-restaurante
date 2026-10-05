"""
services.py — Regras de negócio do sistema de estoque.

Cada função recebe uma Session como primeiro parâmetro (injeção de dependência).
Nunca faz print() nem input() — apenas retorna dados ou lança exceções de erros.py.
"""

# pyrefly: ignore [missing-import]
from sqlalchemy import func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from erros import (
    EstoqueInsuficienteError,
    ItemInativoError,
    ItemNaoEncontradoError,
    QuantidadeInvalidaError,
)
from models import Item, Movimentacao, TipoMovimentacao, MotivoMovimentacao

# ITENS

def cadastrar_item(
    session: Session,
    nome: str,
    unidade: str,
    estoque_minimo: int = 0,
) -> Item:
    """
    Cria um novo item no estoque.

    Args:
        session: sessão do banco aberta por quem chamou.
        nome: nome do item (ex.: "Farinha de Trigo").
        unidade: menor unidade de medida ("g", "ml" ou "un").
        estoque_minimo: quantidade mínima desejada em estoque (default 0).

    Returns:
        O objeto Item recém-criado, já com id preenchido.
    """
    item = Item(
        nome=nome.strip(),
        unidade=unidade.strip().lower(),
        estoque_minimo=estoque_minimo,
    )
    session.add(item)
    session.commit()

    # Após o commit, o SQLAlchemy preenche o id automaticamente.
    # refresh garante que o objeto está sincronizado com o banco.
    session.refresh(item)
    return item


def listar_itens(session: Session, apenas_ativos: bool = True) -> list[Item]:
    """
    Retorna a lista de itens cadastrados.

    Args:
        session: sessão do banco.
        apenas_ativos: se True (padrão), retorna só itens com ativo=True.
                       Se False, retorna todos (útil para administração).

    Returns:
        Lista de objetos Item, ordenada por nome.
    """
    query = session.query(Item)

    if apenas_ativos:
        query = query.filter(Item.ativo == True)

    return query.order_by(Item.nome).all()


def buscar_item_por_id(session: Session, item_id: int) -> Item:
    """
    Busca um item pelo id. Lança exceção se não encontrar.

    Essa função é usada internamente pelas outras funções do services
    para evitar repetir a mesma verificação em vários lugares.

    Args:
        session: sessão do banco.
        item_id: id do item a buscar.

    Returns:
        O objeto Item encontrado.

    Raises:
        ItemNaoEncontradoError: se o item_id não existe no banco.
    """
    item = session.get(Item, item_id)

    if item is None:
        raise ItemNaoEncontradoError(f"Item com id={item_id} nao encontrado.")

    return item


def desativar_item(session: Session, item_id: int) -> Item:
    """
    Marca um item como inativo (soft delete).

    O item permanece no banco com todo o histórico, mas novas
    movimentações nele serão bloqueadas por registrar_movimentacao().

    Raises:
        ItemNaoEncontradoError: se o item_id não existe.
    """
    item = buscar_item_por_id(session, item_id)
    item.ativo = False
    session.commit()
    session.refresh(item)
    return item


def reativar_item(session: Session, item_id: int) -> Item:
    """
    Reativa um item que foi desativado.

    Raises:
        ItemNaoEncontradoError: se o item_id não existe.
    """
    item = buscar_item_por_id(session, item_id)
    item.ativo = True
    session.commit()
    session.refresh(item)
    return item


# MOVIMENTACOES

def calcular_saldo(session: Session, item_id: int) -> int:
    """
    Calcula o saldo atual de um item: soma das entradas - soma das saídas.

    Faz tudo no banco com SQL (SUM), sem trazer todas as movimentações pra memória.
    Se o item não tiver movimentações, retorna 0.

    Args:
        session: sessão do banco.
        item_id: id do item a consultar.

    Returns:
        Saldo atual em inteiro (na menor unidade: g, ml ou un).
    """
    # Soma só as entradas deste item
    total_entradas = (
        session.query(func.coalesce(func.sum(Movimentacao.quantidade), 0))
        .filter(
            Movimentacao.item_id == item_id,
            Movimentacao.tipo == TipoMovimentacao.ENTRADA,
        )
        .scalar()
    )

    # Soma só as saídas deste item
    total_saidas = (
        session.query(func.coalesce(func.sum(Movimentacao.quantidade), 0))
        .filter(
            Movimentacao.item_id == item_id,
            Movimentacao.tipo == TipoMovimentacao.SAIDA,
        )
        .scalar()
    )

    return total_entradas - total_saidas


def registrar_movimentacao(
    session: Session,
    item_id: int,
    tipo: TipoMovimentacao,
    quantidade: int,
    motivo: MotivoMovimentacao,
) -> Movimentacao:
    """
    Registra uma entrada ou saída no estoque, após validar todas as regras.

    Ordem das validações:
    1. Quantidade deve ser > 0
    2. Item deve existir no banco
    3. Item deve estar ativo
    4. Se for SAIDA, saldo não pode ficar negativo

    Se qualquer validação falhar, lança exceção e nada é gravado.

    Args:
        session: sessão do banco.
        item_id: id do item.
        tipo: TipoMovimentacao.ENTRADA ou TipoMovimentacao.SAIDA.
        quantidade: valor positivo na menor unidade.
        motivo: MotivoMovimentacao (COMPRA, USO, PERDA, VENCIMENTO).

    Returns:
        O objeto Movimentacao recém-criado.

    Raises:
        QuantidadeInvalidaError: se quantidade <= 0.
        ItemNaoEncontradoError: se item_id não existe.
        ItemInativoError: se item está desativado.
        EstoqueInsuficienteError: se saída deixaria saldo negativo.
    """
    # 1. Quantidade positiva
    if quantidade <= 0:
        raise QuantidadeInvalidaError(
            f"Quantidade deve ser maior que zero (recebido: {quantidade})."
        )

    # 2. Item existe? (buscar_item_por_id já lança ItemNaoEncontradoError se não)
    item = buscar_item_por_id(session, item_id)

    # 3. Item ativo?
    if not item.ativo:
        raise ItemInativoError(
            f"Item '{item.nome}' (id={item.id}) esta inativo."
        )

    # 4. Se for saída, verificar saldo
    if tipo == TipoMovimentacao.SAIDA:
        saldo_atual = calcular_saldo(session, item_id)
        if saldo_atual < quantidade:
            raise EstoqueInsuficienteError(
                f"Saldo insuficiente para '{item.nome}'. "
                f"Disponivel: {saldo_atual}{item.unidade}, "
                f"solicitado: {quantidade}{item.unidade}."
            )

    # Tudo validado — cria e grava a movimentação
    mov = Movimentacao(
        item_id=item_id,
        tipo=tipo,
        quantidade=quantidade,
        motivo=motivo,
    )
    session.add(mov)
    session.commit()
    session.refresh(mov)
    return mov


def listar_movimentacoes(session: Session, item_id: int) -> list[Movimentacao]:
    """
    Retorna o histórico de movimentações de um item específico,
    ordenado da mais antiga para a mais recente.

    Args:
        session: sessão do banco.
        item_id: id do item.

    Returns:
        Lista de objetos Movimentacao.
    """
    # Garante que o item existe antes de puxar histórico
    buscar_item_por_id(session, item_id)

    return (
        session.query(Movimentacao)
        .filter(Movimentacao.item_id == item_id)
        .order_by(Movimentacao.criado_em.asc())
        .all()
    )

