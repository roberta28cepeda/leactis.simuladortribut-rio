"""Popula as tabelas de parâmetros com os valores do motor de cálculo.

As alíquotas de referência (CBS/IBS) e o cronograma de transição foram
confirmados verbalmente pelo gestor tributarista da equipe Leactis, em
reunião interna (sem ata/registro formal anexado). Isso é uma validação
mais leve do que uma revisão formal artigo por artigo -- registrado aqui
com honestidade no campo `fonte` de cada parâmetro, para que qualquer
pessoa lendo o banco depois saiba exatamente qual foi o nível de
confirmação por trás do número.

As reduções por NCM continuam como PLACEHOLDER (validado_por_tributarista=
False): a lista abaixo é só 2 exemplos ilustrativos, não uma tabela
completa de NCMs da cesta básica/Anexos -- isso não foi o que a reunião
cobriu, e marcar como validado sugeriria (erroneamente) uma lista completa.

Rode com: python -m app.seed_parametros
"""

from app.database import Base, SessionLocal, engine
from app.models import ParametroAliquotaReferencia, ParametroReducaoNcm, ParametroTransicaoAno

FONTE_VALIDADA = (
    "Confirmado verbalmente pelo gestor tributarista da equipe Leactis, em "
    "reunião interna (sem ata/documento formal anexado). Cronograma "
    "2029-2032 também tem respaldo em fonte oficial (Receita Federal, "
    "gov.br/receitafederal, 'Entenda a Reforma Tributária do Consumo' + "
    "art. 128/129 do ADCT, EC 132/2023)."
)
FONTE_ESTIMATIVA_NCM = (
    "Exemplo ilustrativo, NÃO é uma lista oficial/completa de NCMs -- "
    "não coberto pela validação do gestor tributarista. Conferir Anexo I "
    "da LC 214/2025. Ver docs/spec-motor-calculo-ibs-cbs.md."
)

# cbs_referencia, ibs_referencia
ALIQUOTAS_REFERENCIA = {
    2026: (0.009, 0.001),   # ano de teste: CBS 0,9% / IBS 0,1%, mas neutralizado (ver TRANSICAO)
    2027: (0.088, 0.001),   # CBS cheia; IBS ~0,1% já efetivo (fim da neutralidade)
    2028: (0.088, 0.001),
    2029: (0.088, 0.177),   # a partir daqui, IBS na alíquota de referência plena;
    2030: (0.088, 0.177),   # fracao_ibs_ativa (abaixo) controla quanto dela já vigora
    2031: (0.088, 0.177),
    2032: (0.088, 0.177),
    2033: (0.088, 0.177),
}

# fracao_ibs_ativa, fracao_icms_iss_residual, cbs_substitui_pis_cofins, ipi_zerado
TRANSICAO = {
    # 2026: fase de teste -- CBS/IBS incidem em alíquota simbólica mas são
    # compensados com PIS/COFINS e ICMS/ISS pagos no período (carga efetiva
    # neutralizada). Modelamos isso não ativando CBS nem IBS, e mantendo
    # ICMS/ISS/PIS/COFINS/IPI 100% como estão hoje -- resultado líquido: sem
    # mudança, que é o efeito pretendido pela neutralidade.
    2026: (0.0, 1.0, False, False),
    # 2027-2028: CBS substitui PIS/COFINS integralmente; IBS já efetivo (não
    # mais neutralizado), mas na alíquota de referência baixa (~0,1% acima) --
    # por isso fracao_ibs_ativa=1.0 aqui (100% de uma alíquota pequena), não
    # 0.0 como num placeholder anterior. IPI já vai a zero.
    2027: (1.0, 1.0, True, True),
    2028: (1.0, 1.0, True, True),
    # 2029-2032: cronograma do art. 128 do ADCT (fonte oficial). ICMS/ISS
    # residual multiplicado pela fração sobre o valor já destacado na nota
    # (equivalente à "alíquota original"), não descontado ano a ano.
    2029: (0.10, 0.90, True, True),
    2030: (0.20, 0.80, True, True),
    2031: (0.30, 0.70, True, True),
    2032: (0.40, 0.60, True, True),
    2033: (1.0, 0.0, True, True),
}

# Exemplos ilustrativos de redução -- NÃO é uma lista oficial/completa de
# NCMs da cesta básica ou de regimes diferenciados (LC 214/2025, Anexos).
# Continua como placeholder -- ver FONTE_ESTIMATIVA_NCM.
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
                    validado_por_tributarista=True,
                    fonte=FONTE_VALIDADA,
                ))
        if db.query(ParametroTransicaoAno).count() == 0:
            for ano, (ibs_frac, icms_iss_frac, cbs_ativa, ipi_zerado) in TRANSICAO.items():
                db.add(ParametroTransicaoAno(
                    ano=ano, fracao_ibs_ativa=ibs_frac,
                    fracao_icms_iss_residual=icms_iss_frac,
                    cbs_substitui_pis_cofins=cbs_ativa,
                    ipi_zerado=ipi_zerado,
                    validado_por_tributarista=True,
                    fonte=FONTE_VALIDADA,
                ))
        if db.query(ParametroReducaoNcm).count() == 0:
            for prefixo, reducao, desc in REDUCOES_NCM_EXEMPLO:
                db.add(ParametroReducaoNcm(
                    ncm_prefixo=prefixo, percentual_reducao=reducao,
                    descricao=desc, validado_por_tributarista=False,
                    fonte=FONTE_ESTIMATIVA_NCM,
                ))
        db.commit()
        print("Parâmetros inseridos (alíquotas/cronograma validados; reduções por NCM ainda placeholder).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
