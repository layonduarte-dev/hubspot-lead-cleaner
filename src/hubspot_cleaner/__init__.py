"""
cli.py
======

Interface de linha de comando da aplicação. Exemplos:

    # CSV -> xlsx (padrão, sem configuração nenhuma)
    python -m hubspot_cleaner.cli --input samples/leads_sample.csv

    # Google Sheets público -> xlsx
    python -m hubspot_cleaner.cli --input "https://docs.google.com/.../edit"

    # Preservando colunas que você quer tratar à mão depois
    python -m hubspot_cleaner.cli --input leads.csv \\
        --preserve "Observações" --preserve "Origem do Lead"

    # Saída direto no Google Sheets (requer service account)
    python -m hubspot_cleaner.cli --input leads.csv \\
        --output gsheets --share seu-email@gmail.com
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite rodar tanto como módulo (-m) quanto como script direto.
try:
    from .config import load_settings
    from .io_writers import escrever_google_sheets, escrever_xlsx
    from .pipeline import processar
except ImportError:  # execução como script solto
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from hubspot_cleaner.config import load_settings
    from hubspot_cleaner.io_writers import escrever_google_sheets, escrever_xlsx
    from hubspot_cleaner.pipeline import processar


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="hubspot-lead-cleaner",
        description="Higieniza planilhas de leads/contatos para o HubSpot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--input",
        "-i",
        required=True,
        help="Caminho do CSV local ou link do Google Sheets.",
    )
    p.add_argument(
        "--output",
        "-o",
        choices=["xlsx", "gsheets"],
        default="xlsx",
        help="Formato de saída (padrão: xlsx, zero-config).",
    )
    p.add_argument(
        "--output-dir",
        default="output",
        help="Pasta de saída para o .xlsx (padrão: ./output).",
    )
    p.add_argument(
        "--preserve",
        action="append",
        default=[],
        metavar="COLUNA",
        help="Coluna a preservar intacta. Use várias vezes para várias colunas.",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Caminho alternativo para o mapping.yaml.",
    )
    p.add_argument(
        "--gsheets-auth",
        action="store_true",
        help="Ler Google Sheets em modo autenticado (service account).",
    )
    p.add_argument(
        "--share",
        default=None,
        metavar="EMAIL",
        help="E-mail para compartilhar a planilha gerada (saída gsheets).",
    )
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        settings = load_settings(args.config)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    print(f"📥 Lendo entrada: {args.input}")
    try:
        df_dados, df_invalidos, rel = processar(
            origem=args.input,
            settings=settings,
            preservar=args.preserve,
            gsheets_auth=args.gsheets_auth,
        )
    except (ValueError, PermissionError, FileNotFoundError) as e:
        print(f"❌ Erro no processamento: {e}", file=sys.stderr)
        return 1

    log_texto = rel.gerar_log()

    # ---- Escreve a saída no destino escolhido ---------------------------
    if args.output == "gsheets":
        try:
            url = escrever_google_sheets(
                df_dados, df_invalidos, compartilhar_com=args.share
            )
            print(f"\n🔗 Planilha criada no Google Sheets:\n   {url}")
        except (FileNotFoundError, ImportError) as e:
            print(f"❌ Não foi possível usar o Google Sheets: {e}", file=sys.stderr)
            print("   Dica: rode sem --output gsheets para gerar .xlsx.", file=sys.stderr)
            return 1
    else:
        caminho = escrever_xlsx(
            df_dados, df_invalidos, log_texto, pasta_saida=args.output_dir
        )
        print(f"\n💾 Arquivo gerado: {caminho}")

    print(rel.resumo_terminal())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
