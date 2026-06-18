"""
io_readers.py
=============

Entrada da aplicação. Suporta:

    - Arquivo CSV local (com fallback de encoding utf-8 -> latin1).
    - Link do Google Sheets:
        * Modo público: usa a URL de export CSV (sem credenciais).
        * Modo privado/autenticado: usa gspread + service account
          (requer GOOGLE_SERVICE_ACCOUNT_FILE).

Todas as funções devolvem um ``pandas.DataFrame`` cru, sem nenhuma limpeza —
a limpeza é responsabilidade do pipeline.
"""

from __future__ import annotations

import io
import os
import re
from typing import Optional

import pandas as pd
import requests


def ler_csv(caminho: str) -> pd.DataFrame:
    """
    Lê um CSV local. Tenta utf-8-sig primeiro (lida com BOM do Excel) e,
    se falhar, cai para latin1 — cobre a maioria das planilhas brasileiras.
    """
    try:
        return pd.read_csv(caminho, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        return pd.read_csv(caminho, encoding="latin1", dtype=str)


def _extrair_id_planilha(url: str) -> Optional[str]:
    """Extrai o ID da planilha de uma URL do Google Sheets."""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return m.group(1) if m else None


def _extrair_gid(url: str) -> str:
    """Extrai o gid (aba) da URL; usa '0' (primeira aba) como padrão."""
    m = re.search(r"[#&?]gid=(\d+)", url)
    return m.group(1) if m else "0"


def ler_google_sheets_publico(url: str) -> pd.DataFrame:
    """
    Lê uma planilha **pública** do Google Sheets sem credenciais, usando o
    endpoint de export CSV. A planilha precisa estar compartilhada como
    "qualquer pessoa com o link pode ver".
    """
    planilha_id = _extrair_id_planilha(url)
    if not planilha_id:
        raise ValueError(f"Não consegui extrair o ID da planilha da URL: {url}")

    gid = _extrair_gid(url)
    export_url = (
        f"https://docs.google.com/spreadsheets/d/{planilha_id}"
        f"/export?format=csv&gid={gid}"
    )
    resp = requests.get(export_url, timeout=30)
    resp.raise_for_status()

    # Se o Google devolver HTML de login, a planilha não é pública.
    if resp.text.lstrip().lower().startswith("<!doctype html"):
        raise PermissionError(
            "A planilha não parece estar pública. Compartilhe como "
            "'qualquer pessoa com o link' ou use o modo autenticado "
            "(--gsheets-auth) com uma service account."
        )

    return pd.read_csv(io.StringIO(resp.text), dtype=str)


def ler_google_sheets_autenticado(url: str) -> pd.DataFrame:
    """
    Lê uma planilha privada usando gspread + service account.

    Requer a variável de ambiente GOOGLE_SERVICE_ACCOUNT_FILE apontando para
    o JSON de credenciais, e a planilha compartilhada com o e-mail da
    service account.
    """
    import gspread  # import tardio: só carrega se realmente for usado

    cred_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not cred_file or not os.path.exists(cred_file):
        raise FileNotFoundError(
            "GOOGLE_SERVICE_ACCOUNT_FILE não definido ou inexistente. "
            "Defina o caminho do JSON da service account no .env."
        )

    gc = gspread.service_account(filename=cred_file)
    planilha_id = _extrair_id_planilha(url)
    if not planilha_id:
        raise ValueError(f"Não consegui extrair o ID da planilha da URL: {url}")

    planilha = gc.open_by_key(planilha_id)
    aba = planilha.sheet1  # primeira aba
    registros = aba.get_all_records()  # lista de dicts (1ª linha = cabeçalho)
    return pd.DataFrame(registros, dtype=str)


def carregar_entrada(origem: str, gsheets_auth: bool = False) -> pd.DataFrame:
    """
    Detecta automaticamente o tipo de entrada e devolve o DataFrame.

    - URL do Google Sheets -> modo público (ou autenticado se gsheets_auth).
    - Caminho terminando em .csv -> leitura de CSV local.
    """
    origem = origem.strip()
    if "docs.google.com/spreadsheets" in origem:
        if gsheets_auth:
            return ler_google_sheets_autenticado(origem)
        return ler_google_sheets_publico(origem)

    if origem.lower().endswith(".csv"):
        return ler_csv(origem)

    raise ValueError(
        f"Origem não reconhecida: {origem}\n"
        "Use um caminho .csv local ou um link do Google Sheets."
    )
