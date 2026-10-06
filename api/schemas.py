"""
api/schemas.py — Contratos de dados (Pydantic) de entrada e saída.

Garante validação de tipos de dados nas requisições e serialização limpa
das respostas, sem expor os models do SQLAlchemy diretamente.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from models import TipoMovimentacao, MotivoMovimentacao, PapelUsuario


# --- Schemas de Usuário ------------------------------------------------------

class UsuarioCriar(BaseModel):
    """Dados recebidos para cadastrar usuário; senha nunca é devolvida."""
    nome: str = Field(..., description="Nome do usuário")
    login: str = Field(..., description="Login (normalizado pela camada de serviço)")
    senha: str = Field(..., min_length=8, max_length=128, description="Senha de 8 a 128 caracteres")
    papel: PapelUsuario = Field(..., description="ADMINISTRADOR, ESTOQUISTA ou COZINHA")


class UsuarioMudarPapel(BaseModel):
    """Novo papel do usuário."""
    papel: PapelUsuario


class UsuarioResposta(BaseModel):
    """Campos públicos do usuário; senha_hash é deliberadamente omitido."""
    id: int
    nome: str
    login: str
    papel: PapelUsuario
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Item ---------------------------------------------------------

class ItemCriar(BaseModel):
    """Payload de entrada para criação de item."""
    nome: str = Field(..., description="Nome do item (ex: Farinha de Trigo)")
    unidade: str = Field(..., description="Unidade de medida: g, ml ou un")
    estoque_minimo: int = Field(default=0, ge=0, description="Estoque mínimo em menor unidade (>= 0)")


class ItemEditar(BaseModel):
    """Payload de entrada para edição de item."""
    nome: str = Field(..., description="Novo nome do item")
    unidade: str = Field(..., description="Nova unidade de medida: g, ml ou un")
    estoque_minimo: int = Field(..., ge=0, description="Novo estoque mínimo (>= 0)")


class ItemResposta(BaseModel):
    """Dados cadastrais de um item retornados pela API."""
    id: int
    nome: str
    unidade: str
    estoque_minimo: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


class ItemComSaldoResposta(ItemResposta):
    """Item acompanhado do seu saldo atual calculado."""
    saldo: int


class ItemAlertaResposta(BaseModel):
    """Item em estado de alerta com saldo abaixo do estoque mínimo."""
    item: ItemResposta
    saldo_atual: int
    falta: int


# --- Schemas de Movimentação -------------------------------------------------

class MovimentacaoCriar(BaseModel):
    """Payload de entrada para registrar movimentação."""
    item_id: int = Field(..., gt=0, description="ID do item")
    tipo: TipoMovimentacao = Field(..., description="ENTRADA ou SAIDA")
    quantidade: int = Field(..., gt=0, description="Quantidade estritamente positiva na menor unidade")
    motivo: MotivoMovimentacao = Field(..., description="Motivo (COMPRA, USO, PERDA, VENCIMENTO)")


class MovimentacaoResposta(BaseModel):
    """Representação de uma movimentação registrada."""
    id: int
    item_id: int
    tipo: TipoMovimentacao
    quantidade: int
    motivo: MotivoMovimentacao
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class SaldoResposta(BaseModel):
    """Saldo atual consolidado de um item."""
    item_id: int
    saldo: int


# --- Schemas de Erro ---------------------------------------------------------

class ErroResposta(BaseModel):
    """Formato padrão das respostas de erro da aplicação."""
    erro: str
    mensagem: str
