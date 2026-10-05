"""
models.py — Modelos ORM (Item e Movimentacao).

Define a estrutura das tabelas como classes Python.
Sem lógica de negócio aqui — apenas a "forma" dos dados.
"""

import enum
from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

from db import Base


# --- Enums do domínio --------------------------------------------------------
# Usamos Enum do Python para restringir os valores aceitos.
# O SQLAlchemy grava o *nome* do enum como texto no banco (ex.: "ENTRADA").

class TipoMovimentacao(enum.Enum):
    """Define se a movimentação é entrada ou saída de estoque."""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class MotivoMovimentacao(enum.Enum):
    """Categoriza o motivo da movimentação."""
    COMPRA = "COMPRA"
    USO = "USO"
    PERDA = "PERDA"
    VENCIMENTO = "VENCIMENTO"


# --- Modelo: Item ------------------------------------------------------------

class Item(Base):
    """Representa um item do estoque (ex.: Farinha, Azeite, Guardanapo)."""

    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    unidade = Column(String(10), nullable=False)          # "g", "ml" ou "un"
    estoque_minimo = Column(Integer, nullable=False, default=0)  # em menor unidade
    ativo = Column(Boolean, nullable=False, default=True)

    # Relacionamento: um Item tem várias Movimentacoes.
    # back_populates cria a ligação bidirecional (Item.movimentacoes <-> Movimentacao.item).
    movimentacoes = relationship("Movimentacao", back_populates="item")

    def __repr__(self) -> str:
        """Representação útil para debug no terminal."""
        status = "ativo" if self.ativo else "inativo"
        return f"Item(id={self.id}, nome='{self.nome}', unidade='{self.unidade}', {status})"


# --- Modelo: Movimentacao ----------------------------------------------------

class Movimentacao(Base):
    """Representa uma entrada ou saída de estoque."""

    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # FK para itens. ondelete="RESTRICT" impede deletar um item que tem movimentações
    # (mesmo que a gente não delete itens, é uma proteção extra no banco).
    item_id = Column(Integer, ForeignKey("itens.id", ondelete="RESTRICT"), nullable=False)

    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(Integer, nullable=False)  # sempre positivo, em menor unidade
    motivo = Column(Enum(MotivoMovimentacao), nullable=False)

    # timezone.utc garante que o horário é salvo em UTC.
    # O default é uma função (sem parênteses no lambda) — chamada no momento do INSERT.
    criado_em = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relacionamento inverso: Movimentacao.item dá acesso ao objeto Item.
    item = relationship("Item", back_populates="movimentacoes")

    def __repr__(self) -> str:
        return (
            f"Movimentacao(id={self.id}, item_id={self.item_id}, "
            f"tipo={self.tipo.value}, qtd={self.quantidade}, motivo={self.motivo.value})"
        )


# --- Criação das tabelas (para testar) --------------------------------------
if __name__ == "__main__":
    from db import criar_tabelas, engine
    # pyrefly: ignore [missing-import]
    from sqlalchemy import inspect

    criar_tabelas()

    # Mostra as tabelas que existem no banco
    inspetor = inspect(engine)
    tabelas = inspetor.get_table_names()
    print(f"[OK] Tabelas criadas: {tabelas}")

    # Mostra as colunas de cada tabela
    for tabela in tabelas:
        colunas = [col["name"] for col in inspetor.get_columns(tabela)]
        print(f"     {tabela}: {colunas}")
