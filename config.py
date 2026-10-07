"""Configuração de ambiente do projeto.

Lê as variáveis obrigatórias do arquivo .env e falha cedo com uma mensagem clara
quando a chave de assinatura não foi configurada.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _require_env(name: str) -> str:
    """Lê uma variável obrigatória do ambiente и falha com mensagem clara."""
    valor = os.getenv(name)
    if valor is None or not valor.strip():
        raise RuntimeError(
            f"Variável de ambiente obrigatória '{name}' não definida. "
            "Copie o arquivo .env.example para .env e configure o valor antes de iniciar a API."
        )
    return valor.strip()


SECRET_KEY = _require_env("SECRET_KEY")
SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "480"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
