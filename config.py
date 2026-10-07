"""Configuração de ambiente do projeto.

Lê as variáveis obrigatórias do arquivo .env e falha cedo com uma mensagem clara
quando a chave de assinatura não foi configurada.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


def _require_env(name: str) -> str:
    """Lê uma variável obrigatória do ambiente e falha com mensagem clara."""
    valor = os.getenv(name)
    if valor is None or not valor.strip():
        raise RuntimeError(
            f"Variável de ambiente obrigatória '{name}' não definida. "
            "Copie o arquivo .env.example para .env e configure o valor antes de iniciar a API."
        )
    return valor.strip()


def _parse_session_ttl(value: str) -> int:
    """Valida a expiração da sessão em minutos."""
    try:
        minutos = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "SESSION_TTL_MINUTES deve ser um inteiro em minutos. Exemplo: 480 para 8 horas."
        ) from exc

    if minutos <= 0:
        raise ValueError(
            "SESSION_TTL_MINUTES deve ser maior que zero. Exemplo: 480 para 8 horas."
        )
    return minutos


def _parse_cookie_secure(value: str) -> bool:
    """Valida e converte o valor de COOKIE_SECURE."""
    normalizado = value.strip().lower()
    if normalizado in {"1", "true", "yes", "on"}:
        return True
    if normalizado in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(
        "COOKIE_SECURE deve ser um booleano. Use true/false, 1/0, yes/no ou on/off."
    )


SECRET_KEY = _require_env("SECRET_KEY")
SESSION_TTL_MINUTES = _parse_session_ttl(os.getenv("SESSION_TTL_MINUTES", "480"))
COOKIE_SECURE = _parse_cookie_secure(os.getenv("COOKIE_SECURE", "false"))
