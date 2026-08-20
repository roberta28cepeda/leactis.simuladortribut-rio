"""Valida o cronograma 2029-2033 (art. 128 do ADCT) contra o exemplo
numérico da especificação (docs/spec-motor-calculo-ibs-cbs.md, seção 2):

    ICMS nominal de 17% -> 15,3% (2029) / 13,6% (2030) / 11,9% (2031) /
    10,2% (2032) / 0% (2033)

A regra é MULTIPLICATIVA sobre a base original (o valor de ICMS já
destacado na nota), não um desconto acumulado ano a ano -- esse é o ponto
que a spec descreve como "fonte de erro comum". Este teste existe pra
travar essa regra caso alguém reintroduza a versão errada no futuro.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.rules.motor_calculo import calcular_impacto_item
from app.seed_parametros import TRANSICAO


@pytest.fixture
def db_so_icms_iss():
    """Banco com o cronograma real (via TRANSICAO do seed), mas CBS/IBS
    zerados -- isola só o comportamento do resíduo de ICMS/ISS pra
    comparar direto com o exemplo numérico da spec."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for ano in range(2029, 2034):
        session.add(models.ParametroAliquotaReferencia(
            ano=ano, cbs_referencia=0.0, ibs_referencia=0.0, validado_por_tributarista=False,
        ))
        ibs_frac, icms_iss_frac, cbs_ativa, ipi_zerado = TRANSICAO[ano]
        session.add(models.ParametroTransicaoAno(
            ano=ano, fracao_ibs_ativa=ibs_frac, fracao_icms_iss_residual=icms_iss_frac,
            cbs_substitui_pis_cofins=cbs_ativa, ipi_zerado=ipi_zerado, validado_por_tributarista=False,
        ))
    session.commit()
    yield session
    session.close()


def test_reducao_icms_17_por_cento_bate_com_exemplo_da_spec(db_so_icms_iss):
    # ICMS nominal de 17% sobre uma base de R$1000 = R$170,00
    item = models.ItemNota(numero_item=1, valor_produto=1000.0, valor_icms=170.0)

    esperado = {
        2029: 153.0,  # 17% x 0,90
        2030: 136.0,  # 17% x 0,80
        2031: 119.0,  # 17% x 0,70
        2032: 102.0,  # 17% x 0,60
        2033: 0.0,    # extinto
    }

    resultados = calcular_impacto_item(db_so_icms_iss, item, list(esperado.keys()))
    for r in resultados:
        # CBS/IBS zerados neste fixture -> carga_reforma == resíduo de ICMS/ISS puro
        assert r.carga_reforma == pytest.approx(esperado[r.ano], abs=0.01), f"ano {r.ano}"


def test_regra_e_multiplicativa_nao_subtrativa_acumulada(db_so_icms_iss):
    """Trava específica contra o bug que a spec avisa ser comum: se alguém
    implementar como desconto de pontos percentuais acumulado ano a ano em
    vez de fracao(ano) x base_original, este teste falha."""
    item = models.ItemNota(numero_item=1, valor_produto=1000.0, valor_icms=170.0)
    resultados = {r.ano: r.carga_reforma for r in calcular_impacto_item(db_so_icms_iss, item, [2029, 2030, 2031, 2032])}

    # A diferença ano a ano deve ser sempre 17,00 (10 pontos percentuais de
    # 170,00), porque cada ano é 17% x fração -- nunca um desconto
    # acumulado que aceleraria ou desaceleraria a diferença.
    assert resultados[2029] - resultados[2030] == pytest.approx(17.0, abs=0.01)
    assert resultados[2030] - resultados[2031] == pytest.approx(17.0, abs=0.01)
    assert resultados[2031] - resultados[2032] == pytest.approx(17.0, abs=0.01)
