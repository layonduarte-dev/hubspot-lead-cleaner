from __future__ import annotations
import argparse
import sys
from pathlib import Path

try:
    from .config import load_settings
    from .io_writers import escrever_google_sheets, escrever_xlsx
    from .pipeline import processar
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from hubspot_cleaner.config import load_settings
    from hubspot_cleaner.io_writers import escrever_google_sheets, escrever_xlsx
    from hubspot_cleaner.pipeline import processar

def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="hubspot-lead-cleaner")
    p.add_argument("--input", "-i", required=True)
    p.add_argument("--output", "-o", choices=["xlsx", "gsheets"], default="xlsx")
    p.add_argument("--output-dir", default="output")
    p.add_argument("--preserve", action="append", default=[], metavar="COLUNA")
    p.add_argument("--config", default=None)
    p.add_argument("--gsheets-auth", action="store_true")
    p.add_argument("--share", default=None)
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
            origem=args.input, settings=settings,
            preservar=args.preserve, gsheets_auth=args.gsheets_auth,
        )
    except (ValueError, PermissionError, FileNotFoundError) as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        return 1
    log_texto = rel.gerar_log()
    if args.output == "gsheets":
        try:
            url = escrever_google_sheets(df_dados, df_invalidos, compartilhar_com=args.share)
            print(f"\n🔗 Planilha: {url}")
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            return 1
    else:
        caminho = escrever_xlsx(df_dados, df_invalidos, log_texto, pasta_saida=args.output_dir)
        print(f"\n💾 Arquivo gerado: {caminho}")
    print(rel.resumo_terminal())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
