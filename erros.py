"""
erros.py — Exceções customizadas do domínio.

Cada exceção representa uma violação de regra de negócio específica.
A camada de serviço (services.py) lança essas exceções.
A camada de interface (terminal.py ou FastAPI) captura e traduz para o usuário.

Todas herdam de EstoqueError, permitindo capturar qualquer erro do domínio
com um único 'except EstoqueError'.
"""


class EstoqueError(Exception):
    """Classe base para todos os erros de domínio do sistema de estoque."""
    pass


class ItemNaoEncontradoError(EstoqueError):
    """O item_id informado não existe no banco."""
    pass


class ItemInativoError(EstoqueError):
    """Tentou operar em um item que está desativado (ativo=False)."""
    pass


class QuantidadeInvalidaError(EstoqueError):
    """Quantidade informada é zero ou negativa."""
    pass


class EstoqueInsuficienteError(EstoqueError):
    """A saída deixaria o saldo do item negativo."""
    pass


class NomeInvalidoError(EstoqueError):
    """Nome do item vazio ou inválido."""
    pass


class UnidadeInvalidaError(EstoqueError):
    """Unidade de medida fora das permitidas (g, ml, un)."""
    pass


class EstoqueMinimoInvalidoError(EstoqueError):
    """Estoque mínimo informado é negativo."""
    pass


class MotivoIncompativelError(EstoqueError):
    """O motivo informado não é permitido para o tipo de movimentação (ex: ENTRADA com USO)."""
    pass


class AlteracaoUnidadeProibidaError(EstoqueError):
    """Tentativa de alterar a unidade de medida de um item que já possui histórico de movimentações."""
    pass


class LoginDuplicadoError(EstoqueError):
    """O login informado já pertence a outro usuário."""
    pass


class SenhaInvalidaError(EstoqueError):
    """A senha não atende aos requisitos mínimos definidos pelo domínio."""
    pass


class UsuarioNaoEncontradoError(EstoqueError):
    """O usuário informado não existe no banco."""
    pass


class UsuarioInativoError(EstoqueError):
    """O usuário existe, mas está desativado."""
    pass


class UltimoAdministradorError(EstoqueError):
    """A operação deixaria o sistema sem administrador ativo."""
    pass



