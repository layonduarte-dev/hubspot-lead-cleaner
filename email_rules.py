"""
hubspot_cleaner
===============

Pipeline de higienização de planilhas de leads/contatos para importação
no HubSpot.

Regra central: o e-mail é a chave primária. Toda a limpeza gira em torno
de garantir e-mails válidos, únicos e sem lixo, enriquecendo os demais
campos quando possível.

Módulos principais:
    config         -> carrega mapping.yaml e variáveis de ambiente
    io_readers     -> leitura de CSV e Google Sheets
    io_writers     -> escrita em .xlsx e Google Sheets
    header_mapper  -> casa cabeçalhos da entrada com as 8 propriedades-alvo
    email_rules    -> normalização, validação, correção e deduplicação
    name_enrich    -> extração de Nome/Sobrenome a partir do e-mail
    cargo_mapper   -> mapeamento de cargo para a lista oficial (Sólides)
    pipeline       -> orquestra todas as etapas
    report         -> relatório final da operação
"""

__version__ = "1.0.0"
