from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

@dataclass
class Relatorio:
    linhas_entrada: int = 0
    linhas_sem_email: int = 0
    sintaxe_invalida: int = 0
    lixo_removido: int = 0
    duplicatas_removidas: int = 0
    dominios_corrigidos: List[Tuple[str, str]] = field(default_factory=list)
    nomes_enriquecidos: int = 0
    cargos_mapeados: int = 0
    cargos_outros: int = 0
    colunas_preservadas: List[str] = field(default_factory=list)
    linhas_finais: int = 0

    def gerar_log(self) -> str:
        linhas = [
            "RELATÓRIO DE HIGIENIZAÇÃO - HubSpot Lead Cleaner",
            f"Gerado em: {datetime.now():%Y-%m-%d %H:%M:%S}",
            "=" * 55,
            f"Linhas recebidas na entrada........: {self.linhas_entrada}",
            f"Linhas sem e-mail (removidas)......: {self.linhas_sem_email}",
            f"E-mails com sintaxe inválida.......: {self.sintaxe_invalida}",
            f"E-mails de lixo removidos..........: {self.lixo_removido}",
            f"Duplicatas removidas...............: {self.duplicatas_removidas}",
            f"Domínios corrigidos automaticamente: {len(self.dominios_corrigidos)}",
            f"Nomes enriquecidos via e-mail......: {self.nomes_enriquecidos}",
            f"Cargos mapeados (Cargo RH).........: {self.cargos_mapeados}",
            f"  -> classificados como 'Outros'...: {self.cargos_outros}",
            f"Linhas na planilha final...........: {self.linhas_finais}",
            "=" * 55,
        ]
        if self.dominios_corrigidos:
            linhas.append("Exemplos de domínios corrigidos:")
            for antes, depois in self.dominios_corrigidos[:20]:
                linhas.append(f"  {antes} -> {depois}")
        return "\n".join(linhas)

    def resumo_terminal(self) -> str:
        return (
            "\n✅ Higienização concluída!\n"
            f"   Entrada........: {self.linhas_entrada} linhas\n"
            f"   Sem e-mail.....: {self.linhas_sem_email} removidas\n"
            f"   Inválidos......: {self.sintaxe_invalida} sintaxe + {self.lixo_removido} lixo\n"
            f"   Duplicatas.....: {self.duplicatas_removidas} removidas\n"
            f"   Domínios fix...: {len(self.dominios_corrigidos)} corrigidos\n"
            f"   Nomes enriq....: {self.nomes_enriquecidos}\n"
            f"   Cargos.........: {self.cargos_mapeados} mapeados ({self.cargos_outros} em 'Outros')\n"
            f"   ➡️  FINAL.......: {self.linhas_finais} linhas\n"
        )
