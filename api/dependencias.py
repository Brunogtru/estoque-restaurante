"""
api/dependencias.py — Injeção de dependências do FastAPI.

Fornece a sessão de banco de dados por requisição, garantindo
que a conexão seja fechada ao final do ciclo de vida HTTP.
"""

from typing import Generator
from sqlalchemy.orm import Session
from db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependência que abre uma sessão com o banco para cada requisição HTTP
    e garante seu fechamento seguro no bloco finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
