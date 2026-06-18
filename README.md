# ---------------------------------------------------------------------------
# Dependências do HubSpot Lead Cleaner
# Instale com:  pip install -r requirements.txt
# ---------------------------------------------------------------------------

# Núcleo: manipulação de dados e geração de .xlsx
pandas>=2.0,<3.0
openpyxl>=3.1,<4.0
PyYAML>=6.0,<7.0

# Leitura de Google Sheets público (export CSV via HTTP)
requests>=2.31,<3.0

# Saída/entrada autenticada no Google Sheets (OPCIONAL).
# Só é usado se você optar pela integração com a API do Google.
# Pode comentar estas linhas se for usar apenas .xlsx.
gspread>=6.0,<7.0
google-auth>=2.30,<3.0

# Desenvolvimento / testes (opcional)
pytest>=8.0,<9.0
