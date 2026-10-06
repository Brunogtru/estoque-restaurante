"""
api/app.py — Aplicação FastAPI principal e tratador de erros central.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from db import criar_tabelas
from erros import (
    EstoqueError,
    ItemNaoEncontradoError,
    NomeInvalidoError,
    UnidadeInvalidaError,
    EstoqueMinimoInvalidoError,
    QuantidadeInvalidaError,
    EstoqueInsuficienteError,
    ItemInativoError,
    MotivoIncompativelError,
    AlteracaoUnidadeProibidaError,
)
from api.rotas.itens import router as router_itens
from api.rotas.movimentacoes import router as router_movimentacoes


# --- Ciclo de vida da aplicação ----------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Garante que as tabelas do banco existam ao inicializar o servidor."""
    criar_tabelas()
    yield


# --- Instância FastAPI --------------------------------------------------------
app = FastAPI(
    title="Sistema de Controle de Estoque",
    description="API RESTful para controle de estoque de restaurante.",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Mapeamento central de exceções de domínio para HTTP ----------------------
STATUS_POR_EXCECAO = {
    # 404 Not Found: recurso inexistente
    ItemNaoEncontradoError: status.HTTP_404_NOT_FOUND,

    # 422 Unprocessable Entity: dados inválidos de domínio
    NomeInvalidoError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnidadeInvalidaError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    EstoqueMinimoInvalidoError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    QuantidadeInvalidaError: status.HTTP_422_UNPROCESSABLE_CONTENT,

    # 409 Conflict: violação de regra de negócio / estado conflitante
    EstoqueInsuficienteError: status.HTTP_409_CONFLICT,
    ItemInativoError: status.HTTP_409_CONFLICT,
    MotivoIncompativelError: status.HTTP_409_CONFLICT,
    AlteracaoUnidadeProibidaError: status.HTTP_409_CONFLICT,
}


@app.exception_handler(EstoqueError)
async def estoquista_exception_handler(request: Request, exc: EstoqueError):
    """
    Captura qualquer exceção do domínio e converte para JSON padronizado
    com o status HTTP semântico correspondente.
    """
    status_code = STATUS_POR_EXCECAO.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status_code,
        content={
            "erro": exc.__class__.__name__,
            "mensagem": str(exc),
        },
    )


# --- Registro de Rotas -------------------------------------------------------
app.include_router(router_itens)
app.include_router(router_movimentacoes)
