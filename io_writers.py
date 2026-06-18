"""
email_rules.py
==============

O coração da aplicação. O e-mail é a **chave primária**, então este módulo
concentra todas as regras rígidas:

    1. Normalização (trim, minúsculas, pega o 1º e-mail se houver vários)
    2. Correção de typos de domínio (@gmal.com -> @gmail.com)
    3. Validação de sintaxe (regex)
    4. Detecção de lixo (teste@teste.com, asdf@asdf.com, ...)
    5. Deduplicação mantendo o registro mais completo

Cada função recebe e devolve estruturas simples (str / DataFrame) para ser
testável isoladamente.
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from .config import Settings, normalizar

# Regex de sintaxe: "algo@algo.algo", sem espaços e sem @ duplicado.
# Propositalmente simples e previsível — não tenta cobrir a RFC inteira,
# mas pega os erros do mundo real (falta de @, falta de ponto, espaços).
REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Separadores comuns quando há mais de um e-mail na mesma célula.
_SPLIT_RE = re.compile(r"[\s|;,/]+")


def normalizar_email(valor) -> Optional[str]:
    """
    Normaliza uma célula de e-mail.

    - Converte para string, faz strip e lowercase.
    - Remove espaços internos acidentais ("joao @gmail.com").
    - Se houver vários e-mails na célula, devolve o primeiro que contém '@'.
    - Devolve ``None`` para vazios/placeholders ('nan', 'none', '').
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None

    texto = str(valor).strip().lower()
    if texto in ("", "nan", "none", "null", "na"):
        return None

    # Decisão por contagem de '@':
    #   - 1 só '@'  -> espaços são acidentais ("joao @ gmail.com"); remove-os.
    #   - 2+ '@'    -> são vários e-mails na célula; pega o primeiro token.
    if texto.count("@") >= 2:
        for token in _SPLIT_RE.split(texto):
            if "@" in token:
                texto = token
                break

    # Remove espaços internos remanescentes ("joao @ gmail.com").
    texto = texto.replace(" ", "")
    return texto or None


def corrigir_dominio(email: Optional[str], settings: Settings) -> Optional[str]:
    """
    Corrige domínios escritos errado usando o dicionário ``domain_typos``.
    Só altera a parte depois do último '@'.
    """
    if not email or "@" not in email:
        return email
    local, _, dominio = email.rpartition("@")
    correto = settings.domain_typos.get(dominio)
    if correto:
        return f"{local}@{correto}"
    return email


def sintaxe_valida(email: Optional[str]) -> bool:
    """True se o e-mail bate com a regex de sintaxe."""
    if not email:
        return False
    return bool(REGEX_EMAIL.match(email))


def is_lixo(email: Optional[str], settings: Settings) -> bool:
    """
    Detecta e-mails "de lixo" — sintaticamente válidos mas sem sentido.

    Heurísticas:
      - Está na lista explícita ``junk_emails``.
      - Parte local == domínio sem TLD (teste@teste.com, asdf@asdf.x).
      - Local é um único caractere repetido (aaaa@x.com).
      - Local ou domínio são sequências de teclado óbvias (asdf, qwerty).
    """
    if not email or "@" not in email:
        return True

    if normalizar(email) in settings.junk_emails_norm:
        return True

    local, _, dominio = email.rpartition("@")
    dominio_raiz = dominio.split(".")[0]  # "teste" de "teste.com"

    # teste@teste.com, asdf@asdf.org, etc.
    if local == dominio_raiz:
        return True

    # Caractere único repetido na parte local (aaaa, 1111).
    if len(set(local)) == 1 and len(local) >= 1:
        return True

    # Sequências de teclado batidas.
    sequencias = {"asdf", "qwer", "qwerty", "1234", "abcd", "teste", "test"}
    if local in sequencias or dominio_raiz in sequencias:
        return True

    return False


def classificar_email(valor, settings: Settings) -> tuple[Optional[str], bool, str]:
    """
    Aplica o funil completo a uma célula de e-mail.

    Retorna ``(email_limpo, valido, motivo)``:
      - ``email_limpo``: o e-mail após normalização/correção (ou None).
      - ``valido``: True se deve entrar na planilha final.
      - ``motivo``: descrição quando inválido (vai para a aba de inválidos).
    """
    email = normalizar_email(valor)
    if email is None:
        return None, False, "E-mail ausente"

    email = corrigir_dominio(email, settings)

    if not sintaxe_valida(email):
        return email, False, "Sintaxe inválida"

    if is_lixo(email, settings):
        return email, False, "E-mail de lixo/descartável"

    return email, True, ""


def deduplicar(df: pd.DataFrame, email_col: str = "Email") -> pd.DataFrame:
    """
    Remove e-mails duplicados mantendo o registro **mais completo**.

    Critério de desempate, do mais forte para o mais fraco:
      1. Maior número de campos preenchidos (notna).
      2. Maior quantidade de caracteres no total (registro mais "rico").

    Mantém a ordem original na medida do possível e não introduz colunas
    auxiliares no resultado.
    """
    if df.empty or email_col not in df.columns:
        return df

    trabalho = df.copy()
    trabalho["_completude"] = trabalho.notna().sum(axis=1)
    trabalho["_tamanho"] = (
        trabalho.fillna("").astype(str).apply(lambda r: sum(len(v) for v in r), axis=1)
    )

    trabalho = trabalho.sort_values(
        ["_completude", "_tamanho"], ascending=[False, False]
    )
    trabalho = trabalho.drop_duplicates(subset=[email_col], keep="first")
    trabalho = trabalho.drop(columns=["_completude", "_tamanho"])

    # Reordena pelo índice original para previsibilidade.
    return trabalho.sort_index()
