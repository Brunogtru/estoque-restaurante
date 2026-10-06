"""
services.py — Regras de negócio do sistema de estoque.

Cada função recebe uma Session como primeiro parâmetro (injeção de dependência).
Nunca faz print() nem input() — apenas retorna dados ou lança exceções de erros.py.
"""

# pyrefly: ignore [missing-import]
from sqlalchemy import case, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from erros import (
    AlteracaoUnidadeProibidaError,
    EstoqueInsuficienteError,
    EstoqueMinimoInvalidoError,
    ItemInativoError,
    ItemNaoEncontradoError,
    MotivoIncompativelError,
    NomeInvalidoError,
    QuantidadeInvalidaError,
    UnidadeInvalidaError,
)
from models import Item, Movimentacao, TipoMovimentacao, MotivoMovimentacao

UNIDADES_VALIDAS = ("g", "ml", "un")

# Mapeamento estrito: cada Tipo só aceita seu conjunto de Motivos
MOTIVOS_POR_TIPO = {
    TipoMovimentacao.ENTRADA: {MotivoMovimentacao.COMPRA},
    TipoMovimentacao.SAIDA: {
        MotivoMovimentacao.USO,
        MotivoMovimentacao.PERDA,
        MotivoMovimentacao.VENCIMENTO,
    },
}


# ITENS

def _validar_dados_item(nome: str, unidade: str, estoque_minimo: int) -> tuple[str, str]:
    """
    Valida e formata os dados cadastrais de um item.
    Reutilizável tanto para criação quanto para edição.

    Returns:
        Tupla com (nome_limpo, unidade_limpa).

    Raises:
        NomeInvalidoError: se o nome for vazio.
        UnidadeInvalidaError: se a unidade não for g, ml ou un.
        EstoqueMinimoInvalidoError: se o estoque mínimo for negativo.
    """
    nome_limpo = nome.strip() if nome else ""
    if not nome_limpo:
        raise NomeInvalidoError("Nome do item nao pode ser vazio.")

    unidade_limpa = unidade.strip().lower() if unidade else ""
    if unidade_limpa not in UNIDADES_VALIDAS:
        raise UnidadeInvalidaError(
            f"Unidade '{unidade}' invalida. As permitidas sao: {', '.join(UNIDADES_VALIDAS)}."
        )

    if estoque_minimo < 0:
        raise EstoqueMinimoInvalidoError(
            f"Estoque minimo nao pode ser negativo (recebido: {estoque_minimo})."
        )

    return nome_limpo, unidade_limpa


def cadastrar_item(
    session: Session,
    nome: str,
    unidade: str,
    estoque_minimo: int = 0,
) -> Item:
    """
    Cria um novo item no estoque, validando regras antes da inserção.
    """
    nome_limpo, unidade_limpa = _validar_dados_item(nome, unidade, estoque_minimo)

    item = Item(
        nome=nome_limpo,
        unidade=unidade_limpa,
        estoque_minimo=estoque_minimo,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def editar_item(
    session: Session,
    item_id: int,
    nome: str,
    unidade: str,
    estoque_minimo: int,
) -> Item:
    """
    Edita os dados de um item existente (nome, unidade e estoque mínimo).

    Regras de validação:
    1. O item deve existir.
    2. O item deve estar ativo (item inativo não pode ser editado).
    3. Nome não pode ser vazio, unidade deve ser válida e estoque mínimo >= 0.
    4. Só permite mudar a unidade se o item ainda não tiver nenhuma movimentação registrada.

    Raises:
        ItemNaoEncontradoError: se o item_id não existe.
        ItemInativoError: se o item estiver inativo.
        NomeInvalidoError: se o nome for vazio.
        UnidadeInvalidaError: se a unidade for inválida.
        EstoqueMinimoInvalidoError: se estoque_minimo for negativo.
        AlteracaoUnidadeProibidaError: se tentar mudar a unidade com movimentações já existentes.
    """
    # 1. Item existe?
    item = buscar_item_por_id(session, item_id)

    # 2. Item ativo?
    if not item.ativo:
        raise ItemInativoError(
            f"Item '{item.nome}' (id={item.id}) esta inativo e nao pode ser editado. Reative-o primeiro."
        )

    # 3. Validação dos novos dados (reaproveitando a mesma função do cadastro)
    nome_limpo, unidade_limpa = _validar_dados_item(nome, unidade, estoque_minimo)

    # 4. Se a unidade mudou, verificar se existem movimentações registradas
    if unidade_limpa != item.unidade:
        tem_movimentacoes = (
            session.query(Movimentacao.id)
            .filter(Movimentacao.item_id == item_id)
            .first()
            is not None
        )
        if tem_movimentacoes:
            raise AlteracaoUnidadeProibidaError(
                f"Nao e permitido alterar a unidade do item '{item.nome}' de '{item.unidade}' para '{unidade_limpa}', "
                f"pois ja existem movimentacoes registradas."
            )

    # Aplica as alterações
    item.nome = nome_limpo
    item.unidade = unidade_limpa
    item.estoque_minimo = estoque_minimo

    session.commit()
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


def listar_itens_abaixo_do_minimo(session: Session) -> list[tuple[Item, int]]:
    """
    Retorna apenas os itens ATIVOS cujo saldo atual está abaixo do estoque mínimo.

    Executa em UMA ÚNICA CONSULTA SQL (sem loop N+1):
    - Faz um outerjoin de itens com movimentacoes
    - Calcula o saldo com SUM(CASE WHEN tipo='ENTRADA' THEN qtd ELSE -qtd END)
    - Filtra no HAVING apenas onde saldo_calculado < estoque_minimo

    Returns:
        Lista de tuplas (Item, saldo_atual: int), ordenada por nome.
    """
    # Expressão de saldo com sinal (+ entrada, - saída)
    expressao_saldo = func.coalesce(
        func.sum(
            case(
                (Movimentacao.tipo == TipoMovimentacao.ENTRADA, Movimentacao.quantidade),
                (Movimentacao.tipo == TipoMovimentacao.SAIDA, -Movimentacao.quantidade),
                else_=0,
            )
        ),
        0,
    )

    resultados = (
        session.query(Item, expressao_saldo.label("saldo"))
        .outerjoin(Movimentacao, Item.id == Movimentacao.item_id)
        .filter(Item.ativo == True)
        .group_by(Item.id)
        .having(expressao_saldo < Item.estoque_minimo)
        .order_by(Item.nome)
        .all()
    )

    # Retorna lista de tuplas (item, saldo) convertendo saldo para int
    return [(item, int(saldo)) for item, saldo in resultados]



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

    Executa em uma ÚNICA consulta SQL com CASE condicional:
    - Se tipo='ENTRADA', soma +quantidade
    - Se tipo='SAIDA', soma -quantidade
    - Se não houver movimentações, COALESCE retorna 0.

    Args:
        session: sessão do banco.
        item_id: id do item a consultar.

    Returns:
        Saldo atual em inteiro (na menor unidade: g, ml ou un).
    """
    saldo = (
        session.query(
            func.coalesce(
                func.sum(
                    case(
                        (Movimentacao.tipo == TipoMovimentacao.ENTRADA, Movimentacao.quantidade),
                        (Movimentacao.tipo == TipoMovimentacao.SAIDA, -Movimentacao.quantidade),
                        else_=0,
                    )
                ),
                0,
            )
        )
        .filter(Movimentacao.item_id == item_id)
        .scalar()
    )

    return int(saldo)



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
    2. Motivo deve ser compatível com o tipo (ENTRADA só COMPRA; SAIDA só USO/PERDA/VENCIMENTO)
    3. Item deve existir no banco
    4. Item deve estar ativo
    5. Se for SAIDA, saldo não pode ficar negativo

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
        MotivoIncompativelError: se motivo não é permitido para o tipo.
        ItemNaoEncontradoError: se item_id não existe.
        ItemInativoError: se item está desativado.
        EstoqueInsuficienteError: se saída deixaria saldo negativo.
    """
    # 1. Quantidade positiva
    if quantidade <= 0:
        raise QuantidadeInvalidaError(
            f"Quantidade deve ser maior que zero (recebido: {quantidade})."
        )

    # 2. Motivo compatível com o Tipo
    motivos_permitidos = MOTIVOS_POR_TIPO.get(tipo, set())
    if motivo not in motivos_permitidos:
        permitidos_str = ", ".join(m.value for m in motivos_permitidos)
        raise MotivoIncompativelError(
            f"Motivo '{motivo.value}' incompativel com movimentacao de {tipo.value}. "
            f"Motivos permitidos: {permitidos_str}."
        )

    # 3. Item existe? (buscar_item_por_id já lança ItemNaoEncontradoError se não)
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

