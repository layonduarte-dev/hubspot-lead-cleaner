"""
name_enrich.py
==============

Quando a planilha não traz o nome do contato, tentamos extrair Nome e
Sobrenome a partir do **prefixo do e-mail** (a parte antes do '@').

Exemplos:
    joao.silva@empresa.com   -> Nome="Joao",  Sobrenome="Silva"
    maria_souza@x.com.br     -> Nome="Maria", Sobrenome="Souza"
    contato@empresa.com      -> não extrai (prefixo genérico)
    vendas123@x.com          -> não extrai (prefixo genérico)

Princípio: ser **conservador**. É melhor deixar o nome em branco do que
preencher com lixo (ex.: "Joao123" ou "Contato"). Nomes errados sujam a
base e ficam difíceis de detectar depois.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

from .config import Settings, normalizar

# Preposições que devem ficar em minúsculas no Title Case português.
_MINUSCULAS = {"de", "da", "do", "das", "dos", "e"}

# Separadores válidos dentro de um prefixo de e-mail.
_SEP_RE = re.compile(r"[._\-]+")


def _title_case_pt(palavra: str) -> str:
    """Capitaliza respeitando preposições (não usado na 1ª palavra)."""
    return palavra.capitalize()


def _eh_prefixo_generico(prefixo: str, settings: Settings) -> bool:
    """
    True se o prefixo for uma caixa institucional (contato, vendas, rh...).

    Também trata variações com números/sufixos: "vendas2", "rh-sp" etc.,
    comparando a primeira "palavra" do prefixo contra a lista.
    """
    norm = normalizar(prefixo)
    if norm in settings.generic_prefixes_norm:
        return True
    # Primeira palavra antes de separador/numero: "vendas2" -> "vendas".
    primeira = re.split(r"[._\-0-9]+", norm)[0]
    return primeira in settings.generic_prefixes_norm


def _limpar_token(token: str) -> str:
    """Remove dígitos das pontas de um token (joao123 -> joao)."""
    return re.sub(r"^\d+|\d+$", "", token)


def _parece_nome(token: str) -> bool:
    """
    Heurística: um token vira nome se, após remover dígitos das pontas, for
    puramente alfabético e tiver pelo menos 2 letras.
    Descarta "x", "123", "j04o" (dígito no meio).
    """
    limpo = _limpar_token(token)
    return limpo.isalpha() and len(limpo) >= 2


def extrair_nome_do_email(
    email: Optional[str], settings: Settings
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrai ``(Nome, Sobrenome)`` do prefixo do e-mail.

    Devolve ``(None, None)`` quando:
      - o e-mail é inválido;
      - o prefixo é genérico (contato@, vendas@, rh@...);
      - não há tokens que pareçam nome.

    Quando há só um token de nome, devolve ``(Nome, None)``.
    """
    if not email or "@" not in email:
        return None, None

    prefixo = email.split("@", 1)[0]

    if _eh_prefixo_generico(prefixo, settings):
        return None, None

    # Quebra o prefixo em tokens por '.', '_' ou '-' e limpa dígitos das pontas.
    tokens = [_limpar_token(t) for t in _SEP_RE.split(prefixo) if t]

    # Filtra só os tokens que parecem nome de pessoa.
    nomes = [t for t in tokens if t.isalpha() and len(t) >= 2]
    if not nomes:
        return None, None

    if len(nomes) == 1:
        return _title_case_pt(nomes[0]), None

    nome = _title_case_pt(nomes[0])
    # Demais tokens viram o sobrenome, com preposições em minúsculas.
    resto = [
        t.lower() if t.lower() in _MINUSCULAS else _title_case_pt(t)
        for t in nomes[1:]
    ]
    sobrenome = " ".join(resto)
    return nome, sobrenome


def preencher_nomes_faltantes(df, settings: Settings) -> int:
    """
    Percorre o DataFrame e preenche Nome/Sobrenome **apenas** nas linhas em
    que ambos estão vazios, usando o e-mail como fonte.

    Não sobrescreve nomes que já vieram na planilha.
    Retorna a quantidade de linhas enriquecidas (para o relatório).
    """
    import pandas as pd

    enriquecidos = 0
    for idx, linha in df.iterrows():
        nome_atual = linha.get("Nome")
        sobrenome_atual = linha.get("Sobrenome")

        tem_nome = pd.notna(nome_atual) and str(nome_atual).strip() != ""
        tem_sobrenome = pd.notna(sobrenome_atual) and str(sobrenome_atual).strip() != ""
        if tem_nome or tem_sobrenome:
            continue  # já tem nome -> não mexe

        nome, sobrenome = extrair_nome_do_email(linha.get("Email"), settings)
        if nome:
            df.at[idx, "Nome"] = nome
            if sobrenome:
                df.at[idx, "Sobrenome"] = sobrenome
            enriquecidos += 1

    return enriquecidos
