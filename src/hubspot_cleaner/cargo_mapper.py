"""
header_mapper.py
================

Casa os cabeçalhos da planilha de entrada com as 8 propriedades-alvo do
HubSpot. Faz isso em duas camadas:

    1. Sinônimo exato (após normalizar): "e-mail", "mail" -> "Email".
    2. Similaridade aproximada (difflib): pega erros de digitação e
       variações não previstas, desde que acima de ``fuzzy_threshold``.

O resultado é um dicionário ``{cabecalho_original: propriedade_alvo}`` que o
pipeline usa para renomear as colunas. Colunas que não casam com nada são
deixadas como estão (e podem ser preservadas via parâmetro do usuário).
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, List

from .config import Settings, normalizar


def _similaridade(a: str, b: str) -> float:
    """Razão de similaridade 0..1 entre duas strings normalizadas."""
    return SequenceMatcher(None, a, b).ratio()


def mapear_cabecalhos(
    cabecalhos: List[str], settings: Settings
) -> Dict[str, str]:
    """
    Recebe a lista de cabeçalhos do arquivo e devolve o dicionário de
    renomeação para as propriedades-alvo.

    Regras:
      - Cada propriedade-alvo é atribuída a no máximo um cabeçalho (o melhor).
      - Um cabeçalho que já é exatamente uma propriedade-alvo é mantido.
      - Empates são resolvidos pelo maior score; em caso de score igual,
        vence o primeiro cabeçalho encontrado.
    """
    # Pré-calcula a forma normalizada de cada sinônimo para cada alvo.
    alvo_por_sinonimo: Dict[str, str] = {}
    for alvo, sinonimos in settings.header_synonyms.items():
        alvo_por_sinonimo[normalizar(alvo)] = alvo
        for s in sinonimos:
            alvo_por_sinonimo[normalizar(s)] = alvo

    # Para cada propriedade-alvo, guardamos a melhor candidata encontrada.
    melhor_por_alvo: Dict[str, tuple[str, float]] = {}

    for cab in cabecalhos:
        cab_norm = normalizar(cab)
        if not cab_norm:
            continue

        # Camada 1: correspondência exata de sinônimo.
        if cab_norm in alvo_por_sinonimo:
            alvo = alvo_por_sinonimo[cab_norm]
            _considerar(melhor_por_alvo, alvo, cab, 1.0)
            continue

        # Camada 2: melhor similaridade contra todos os sinônimos.
        melhor_alvo, melhor_score = None, 0.0
        for sin_norm, alvo in alvo_por_sinonimo.items():
            score = _similaridade(cab_norm, sin_norm)
            if score > melhor_score:
                melhor_alvo, melhor_score = alvo, score

        if melhor_alvo and melhor_score >= settings.fuzzy_threshold:
            _considerar(melhor_por_alvo, melhor_alvo, cab, melhor_score)

    # Monta o dicionário final {cabecalho_original: alvo}.
    return {cab: alvo for alvo, (cab, _score) in melhor_por_alvo.items()}


def _considerar(
    melhor_por_alvo: Dict[str, tuple[str, float]],
    alvo: str,
    cabecalho: str,
    score: float,
) -> None:
    """Atualiza o melhor candidato de um alvo se este score for maior."""
    atual = melhor_por_alvo.get(alvo)
    if atual is None or score > atual[1]:
        melhor_por_alvo[alvo] = (cabecalho, score)
