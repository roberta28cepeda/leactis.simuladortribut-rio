"""Popula as tabelas de parâmetros com valores PLACEHOLDER, só para permitir
rodar o sistema de ponta a ponta antes da validação com um tributarista.

⚠️ NENHUM valor aqui foi validado. Todos ficam com
validado_por_tributarista=False de propósito -- a API e o frontend exibem
um aviso sempre que algum parâmetro usado numa análise não foi validado.

Rode com: python -m app.seed_parametros
"""

from app.database import Base, SessionLocal, engine
from app.models import ParametroAliquotaReferencia, ParametroReducaoNcm, ParametroTransicaoAno

# Alíquotas de referência estimadas -- mesma ordem de grandeza usada em
# discussões públicas sobre a LC 214/2025 (CBS ~8,8% / IBS ~17,7%, soma de
# referência ~26,5%), mas o valor final depende de resolução do Senado.
# NÃO é uma fonte oficial.
ALIQUOTAS_REFERENCIA = {
    2026: (0.009, 0.001),   # ano de teste: CBS 0,9% / IBS 0,1% (compensável)
    2027: (0.088, 0.001),
    2028: (0.088, 0.001),
    2029: (0.088, 0.177),
    2030: (0.088, 0.177),
    2031: (0.088, 0.177),
    2032: (0.088, 0.177),
    2033: (0.088, 0.177),
}

# fracao_ibs_ativa, fracao_icms_iss_residual, cbs_substitui_pis_cofins
TRANSICAO = {
    2026: (0.0, 1.0, False),   # ano de teste, sem substituição de PIS/Cofins ainda
    2027: (0.0, 1.0, True),
    2028: (0.0, 1.0, True),
    2029: (0.10, 0.90, True),
    2030: (0.20, 0.80, True),
    2031: (0.30, 0.70, True),
    2032: (0.40, 0.60, True),
    2033: (1.0, 0.0, True),
}

# Exemplos ilustrativos de redução -- NÃO é uma lista oficial/completa de
# NCMs da cesta básica ou de regimes diferenciados (LC 214/2025, Anexos).
REDUCOES_NCM_EXEMPLO = [
    ("1006", 1.00, "Arroz (cesta básica -- exemplo ilustrativo, conferir Anexo I da LC 214/2025)"),
    ("0713", 1.00, "Feijão (cesta básica -- exemplo ilustrativo)"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(ParametroAliquotaReferencia).count() == 0:
            for ano, (cbs, ibs) in ALIQUOTAS_REFERENCIA.items():
                db.add(ParametroAliquotaReferencia(
                    ano=ano, cbs_referencia=cbs, ibs_referencia=ibs,
                    validado_por_tributarista=False,
                    fonte="PLACEHOLDER -- não validado, ver README.md",
                ))
        if db.query(ParametroTransicaoAno).count() == 0:
            for ano, (ibs_frac, icms_iss_frac, cbs_ativa) in TRANSICAO.items():
                db.add(ParametroTransicaoAno(
                    ano=ano, fracao_ibs_ativa=ibs_frac,
                    fracao_icms_iss_residual=icms_iss_frac,
                    cbs_substitui_pis_cofins=cbs_ativa,
                    validado_por_tributarista=False,
                    fonte="PLACEHOLDER -- não validado, ver README.md",
                ))
        if db.query(ParametroReducaoNcm).count() == 0:
            for prefixo, reducao, desc in REDUCOES_NCM_EXEMPLO:
                db.add(ParametroReducaoNcm(
                    ncm_prefixo=prefixo, percentual_reducao=reducao,
                    descricao=desc, validado_por_tributarista=False,
                    fonte="PLACEHOLDER -- não validado, ver README.md",
                ))
        db.commit()
        print("Parâmetros placeholder inseridos (todos validado_por_tributarista=False).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
