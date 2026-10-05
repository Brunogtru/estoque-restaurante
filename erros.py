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
