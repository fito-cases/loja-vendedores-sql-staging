"""Data de hoje no fuso horário da loja (FUSO_LOJA no .env).

Fica em um módulo próprio para que os testes possam fixar a data de hoje.
"""
import datetime
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()


def hoje_na_loja():
    """Data atual no fuso da loja (padrão: America/Sao_Paulo)."""
    nome_do_fuso = os.environ.get('FUSO_LOJA', 'America/Sao_Paulo').strip()
    try:
        fuso = ZoneInfo(nome_do_fuso)
    except ZoneInfoNotFoundError:
        raise RuntimeError(
            f'Fuso horário "{nome_do_fuso}" não encontrado. Confira FUSO_LOJA no .env '
            'e se as dependências foram instaladas com: '
            'python -m pip install -r requirements.txt (no Windows, elas incluem tzdata)'
        ) from None
    return datetime.datetime.now(fuso).date()
