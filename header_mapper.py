"""
config.py
=========

Carrega a configuração do pipeline a partir de ``config/mapping.yaml`` e
expõe um objeto ``Settings`` simples para o resto da aplicação consumir.

Centralizar a configuração aqui mantém o código limpo: nenhum outro módulo
precisa saber o caminho do YAML nem como ele é estruturado.
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml

# Caminho padrão do YAML: <raiz_do_projeto>/config/mapping.yaml
# __file__ = .../src/hubspot_cleaner/config.py  ->  sobe 3 níveis até a raiz.
_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "mapping.yaml"
)


def normalizar(texto: str) -> str:
    """
    Normaliza um texto para comparação robusta:
    minúsculas + sem acentos + sem espaços nas pontas.

    Usada tanto no casamento de cabeçalhos quanto no mapeamento de cargos.
    """
    if not texto or not isinstance(texto, str):
        return ""
    texto = texto.strip().lower()
    # Decompõe os acentos (ex.: "á" -> "a" + acento) e remove os acentos.
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


@dataclass
class Settings:
    """Configuração já carregada e pronta para uso."""

    header_synonyms: Dict[str, List[str]] = field(default_factory=dict)
    fuzzy_threshold: float = 0.82
    domain_typos: Dict[str, str] = field(default_factory=dict)
    junk_emails: List[str] = field(default_factory=list)
    generic_prefixes: List[str] = field(default_factory=list)

    # Lista canônica das 8 propriedades-alvo do HubSpot, na ordem de saída.
    target_properties: List[str] = field(
        default_factory=lambda: [
            "Nome",
            "Sobrenome",
            "Email",
            "Número de Telefone",
            "Nome da Empresa",
            "Cargo",
            "Cargo RH",
            "Faixa de Colaboradores",
        ]
    )

    @property
    def junk_emails_norm(self) -> set:
        """Conjunto de e-mails de lixo já normalizados (para lookup O(1))."""
        return {normalizar(e) for e in self.junk_emails}

    @property
    def generic_prefixes_norm(self) -> set:
        """Conjunto de prefixos genéricos normalizados."""
        return {normalizar(p) for p in self.generic_prefixes}


def load_settings(config_path: str | os.PathLike | None = None) -> Settings:
    """
    Lê o YAML de configuração e devolve um objeto ``Settings``.

    Se ``config_path`` não for informado, usa o caminho padrão dentro do
    repositório. Falha de forma clara se o arquivo não existir.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {path}\n"
            "Verifique se config/mapping.yaml existe na raiz do projeto."
        )

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    return Settings(
        header_synonyms=raw.get("header_synonyms", {}),
        fuzzy_threshold=float(raw.get("fuzzy_threshold", 0.82)),
        domain_typos=raw.get("domain_typos", {}),
        junk_emails=raw.get("junk_emails", []),
        generic_prefixes=raw.get("generic_prefixes", []),
    )
