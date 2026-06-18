import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hubspot_cleaner import email_rules
from hubspot_cleaner.config import load_settings
CONFIG = Path(__file__).resolve().parents[1] / "config" / "mapping.yaml"
settings = load_settings(CONFIG)

@pytest.mark.parametrize("entrada,esperado", [
    ("  JOAO@EMPRESA.COM ", "joao@empresa.com"),
    ("joao @gmail.com", "joao@gmail.com"),
    ("", None), ("nan", None), (None, None),
])
def test_normalizar_email(entrada, esperado):
    assert email_rules.normalizar_email(entrada) == esperado

@pytest.mark.parametrize("entrada,esperado", [
    ("joao@gmal.com", "joao@gmail.com"),
    ("ok@gmail.com", "ok@gmail.com"),
])
def test_corrigir_dominio(entrada, esperado):
    assert email_rules.corrigir_dominio(entrada, settings) == esperado

def test_deduplicar_mantem_mais_completo():
    df = pd.DataFrame({"Email": ["joao@x.com","joao@x.com"], "Nome": [None,"Joao"]})
    out = email_rules.deduplicar(df, "Email")
    assert len(out) == 1
    assert out.iloc[0]["Nome"] == "Joao"
