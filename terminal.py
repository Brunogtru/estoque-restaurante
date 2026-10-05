"""
terminal.py — Interface do usuario no terminal.

Responsabilidades:
- Exibir menus e ler input do usuario
- Converter inputs para os tipos corretos
- Chamar funcoes do services.py
- Capturar excecoes do dominio e exibir mensagens amigaveis

Regra: NUNCA tem logica de negocio aqui. So traduz entre humano e servico.
"""

from db import Session
from erros import EstoqueError
from services import (
    cadastrar_item,
    listar_itens,
    buscar_item_por_id,
    desativar_item,
    reativar_item,
    calcular_saldo,
    registrar_movimentacao,
    listar_movimentacoes,
)
from models import TipoMovimentacao, MotivoMovimentacao


# =============================================================================
# HELPERS (funcoes auxiliares para evitar repeticao)
# =============================================================================

def _ler_inteiro(prompt: str) -> int | None:
    """
    Le um inteiro do usuario. Retorna None se a entrada for invalida.
    Isso permite que quem chamou decida o que fazer (repetir, voltar, etc.).
    """
    texto = input(prompt).strip()
    try:
        return int(texto)
    except ValueError:
        print(f"[ERRO] '{texto}' nao e um numero valido.")
        return None


def _pausar():
    """Pausa para o usuario ler a mensagem antes de voltar ao menu."""
    input("\nPressione ENTER para continuar...")


# =============================================================================
# SUBMENU: ITENS
# =============================================================================

def _tela_cadastrar_item():
    """Coleta dados e cadastra um novo item."""
    print("\n--- Cadastrar Novo Item ---")

    nome = input("Nome do item: ").strip()
    if not nome:
        print("[ERRO] Nome nao pode ser vazio.")
        return

    unidade = input("Unidade (g / ml / un): ").strip().lower()
    if unidade not in ("g", "ml", "un"):
        print(f"[ERRO] Unidade '{unidade}' invalida. Use g, ml ou un.")
        return

    estoque_minimo = _ler_inteiro("Estoque minimo (ou 0): ")
    if estoque_minimo is None:
        return
    if estoque_minimo < 0:
        print("[ERRO] Estoque minimo nao pode ser negativo.")
        return

    with Session() as session:
        item = cadastrar_item(session, nome, unidade, estoque_minimo)
        print(f"\n[OK] Item cadastrado: {item}")


def _tela_listar_itens():
    """Exibe a lista de itens com saldo atual."""
    print("\n--- Itens Cadastrados ---")

    with Session() as session:
        itens = listar_itens(session, apenas_ativos=False)

        if not itens:
            print("  Nenhum item cadastrado.")
            return

        # Cabecalho da tabela
        print(f"  {'ID':<5} {'Nome':<25} {'Un':<5} {'Saldo':<10} {'Min':<10} {'Status'}")
        print(f"  {'-'*5} {'-'*25} {'-'*5} {'-'*10} {'-'*10} {'-'*8}")

        for item in itens:
            saldo = calcular_saldo(session, item.id)
            status = "ativo" if item.ativo else "INATIVO"

            # Alerta visual se saldo abaixo do minimo
            alerta = " [!]" if saldo < item.estoque_minimo and item.ativo else ""

            print(
                f"  {item.id:<5} {item.nome:<25} {item.unidade:<5} "
                f"{saldo:<10} {item.estoque_minimo:<10} {status}{alerta}"
            )


def _tela_desativar_item():
    """Desativa um item (soft delete)."""
    print("\n--- Desativar Item ---")

    item_id = _ler_inteiro("ID do item a desativar: ")
    if item_id is None:
        return

    try:
        with Session() as session:
            item = desativar_item(session, item_id)
            print(f"\n[OK] Item desativado: {item}")
    except EstoqueError as e:
        print(f"[ERRO] {e}")


def _tela_reativar_item():
    """Reativa um item desativado."""
    print("\n--- Reativar Item ---")

    item_id = _ler_inteiro("ID do item a reativar: ")
    if item_id is None:
        return

    try:
        with Session() as session:
            item = reativar_item(session, item_id)
            print(f"\n[OK] Item reativado: {item}")
    except EstoqueError as e:
        print(f"[ERRO] {e}")


def menu_itens():
    """Submenu de gerenciamento de itens."""
    while True:
        print("\n========== ITENS ==========")
        print("  1. Cadastrar item")
        print("  2. Listar itens")
        print("  3. Desativar item")
        print("  4. Reativar item")
        print("  0. Voltar")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            _tela_cadastrar_item()
        elif opcao == "2":
            _tela_listar_itens()
        elif opcao == "3":
            _tela_desativar_item()
        elif opcao == "4":
            _tela_reativar_item()
        elif opcao == "0":
            break
        else:
            print("[ERRO] Opcao invalida.")

        _pausar()


# =============================================================================
# SUBMENU: MOVIMENTACOES
# =============================================================================

def _tela_registrar_entrada():
    """Registra entrada de estoque de um item."""
    print("\n--- Registrar Entrada ---")
    item_id = _ler_inteiro("ID do item: ")
    if item_id is None:
        return

    quantidade = _ler_inteiro("Quantidade a entrar: ")
    if quantidade is None:
        return

    print("Motivos disponiveis: COMPRA")
    motivo_str = input("Motivo [COMPRA]: ").strip().upper() or "COMPRA"
    try:
        motivo = MotivoMovimentacao[motivo_str]
    except KeyError:
        print(f"[ERRO] Motivo '{motivo_str}' invalido.")
        return

    try:
        with Session() as session:
            mov = registrar_movimentacao(
                session=session,
                item_id=item_id,
                tipo=TipoMovimentacao.ENTRADA,
                quantidade=quantidade,
                motivo=motivo,
            )
            saldo = calcular_saldo(session, item_id)
            print(f"\n[OK] Entrada registrada com sucesso!")
            print(f"     Item: {mov.item.nome} | Qtd: +{mov.quantidade}{mov.item.unidade} | Novo saldo: {saldo}{mov.item.unidade}")
    except EstoqueError as e:
        print(f"[ERRO] {e}")


def _tela_registrar_saida():
    """Registra saída de estoque de um item."""
    print("\n--- Registrar Saida ---")
    item_id = _ler_inteiro("ID do item: ")
    if item_id is None:
        return

    quantidade = _ler_inteiro("Quantidade a sair: ")
    if quantidade is None:
        return

    print("Motivos disponiveis: USO, PERDA, VENCIMENTO")
    motivo_str = input("Motivo [USO]: ").strip().upper() or "USO"
    try:
        motivo = MotivoMovimentacao[motivo_str]
    except KeyError:
        print(f"[ERRO] Motivo '{motivo_str}' invalido.")
        return

    try:
        with Session() as session:
            mov = registrar_movimentacao(
                session=session,
                item_id=item_id,
                tipo=TipoMovimentacao.SAIDA,
                quantidade=quantidade,
                motivo=motivo,
            )
            saldo = calcular_saldo(session, item_id)
            print(f"\n[OK] Saida registrada com sucesso!")
            print(f"     Item: {mov.item.nome} | Qtd: -{mov.quantidade}{mov.item.unidade} | Novo saldo: {saldo}{mov.item.unidade}")
    except EstoqueError as e:
        print(f"[ERRO] {e}")


def _tela_extrato_item():
    """Exibe o histórico de movimentações e o saldo de um item específico."""
    print("\n--- Extrato / Historico de Movimentacoes ---")
    item_id = _ler_inteiro("ID do item: ")
    if item_id is None:
        return

    try:
        with Session() as session:
            item = buscar_item_por_id(session, item_id)
            movs = listar_movimentacoes(session, item_id)
            saldo = calcular_saldo(session, item_id)

            print(f"\nItem: {item.nome} (ID: {item.id}) | Unidade: {item.unidade}")
            print(f"Status: {'ativo' if item.ativo else 'INATIVO'} | Saldo atual: {saldo}{item.unidade}")
            print(f"Estoque minimo: {item.estoque_minimo}{item.unidade}")

            if not movs:
                print("\n  Nenhuma movimentacao registrada para este item.")
                return

            print(f"\n  {'ID':<5} {'Data/Hora (UTC)':<20} {'Tipo':<10} {'Quantidade':<12} {'Motivo'}")
            print(f"  {'-'*5} {'-'*20} {'-'*10} {'-'*12} {'-'*10}")

            for m in movs:
                sinal = "+" if m.tipo == TipoMovimentacao.ENTRADA else "-"
                qtd_str = f"{sinal}{m.quantidade}{item.unidade}"
                dt_str = m.criado_em.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {m.id:<5} {dt_str:<20} {m.tipo.value:<10} {qtd_str:<12} {m.motivo.value}")
    except EstoqueError as e:
        print(f"[ERRO] {e}")


def menu_movimentacoes():
    """Submenu de movimentações de estoque."""
    while True:
        print("\n======= MOVIMENTACOES =======")
        print("  1. Registrar Entrada")
        print("  2. Registrar Saida")
        print("  3. Extrato / Historico de Item")
        print("  0. Voltar")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            _tela_registrar_entrada()
        elif opcao == "2":
            _tela_registrar_saida()
        elif opcao == "3":
            _tela_extrato_item()
        elif opcao == "0":
            break
        else:
            print("[ERRO] Opcao invalida.")

        _pausar()



# =============================================================================
# MENU PRINCIPAL
# =============================================================================

def menu_principal():
    """Loop principal do sistema."""
    while True:
        print("\n============================")
        print("   CONTROLE DE ESTOQUE")
        print("============================")
        print("  1. Itens")
        print("  2. Movimentacoes")
        print("  0. Sair")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            menu_itens()
        elif opcao == "2":
            menu_movimentacoes()
        elif opcao == "0":
            print("\nAte logo!")
            break
        else:
            print("[ERRO] Opcao invalida.")
