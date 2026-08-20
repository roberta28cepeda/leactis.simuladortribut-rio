import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.rules.motor_calculo import calcular_impacto_item, calcular_impacto_analise, carga_tributaria_atual


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Parâmetros simples e redondos, fáceis de conferir na mão.
    session.add(models.ParametroAliquotaReferencia(
        ano=2027, cbs_referencia=0.10, ibs_referencia=0.20, validado_por_tributarista=True,
    ))
    session.add(models.ParametroTransicaoAno(
        ano=2027, fracao_ibs_ativa=0.0, fracao_icms_iss_residual=1.0,
        cbs_substitui_pis_cofins=True, validado_por_tributarista=True,
    ))
    session.add(models.ParametroAliquotaReferencia(
        ano=2033, cbs_referencia=0.10, ibs_referencia=0.20, validado_por_tributarista=True,
    ))
    session.add(models.ParametroTransicaoAno(
        ano=2033, fracao_ibs_ativa=1.0, fracao_icms_iss_residual=0.0,
        cbs_substitui_pis_cofins=True, validado_por_tributarista=True,
    ))
    session.add(models.ParametroReducaoNcm(
        ncm_prefixo="1006", percentual_reducao=1.0, descricao="teste", validado_por_tributarista=True,
    ))
    session.commit()
    yield session
    session.close()


def _item(valor_produto, ncm=None, icms=0, ipi=0, pis=0, cofins=0, issqn=0):
    return models.ItemNota(
        numero_item=1, valor_produto=valor_produto, ncm=ncm,
        valor_icms=icms, valor_ipi=ipi, valor_pis=pis, valor_cofins=cofins, valor_issqn=issqn,
    )


def test_carga_tributaria_atual_soma_todos_os_tributos():
    item = _item(1000, icms=180, pis=16.5, cofins=76, ipi=0, issqn=0)
    assert carga_tributaria_atual(item) == pytest.approx(272.5)


def test_2027_icms_pleno_e_ibs_ainda_zero(db):
    # Em 2027: fracao_ibs_ativa=0 -> IBS não pesa; ICMS/PIS/COFINS residual
    # (fracao_icms_iss_residual=1) continuam cobrados; CBS (10%) substitui
    # PIS/COFINS.
    item = _item(1000, icms=180, pis=16.5, cofins=76)
    resultado = calcular_impacto_item(db, item, [2027])[0]

    # cbs = 1000*0.10 = 100 ; ibs = 1000*0.20*0 = 0
    # icms_iss_residual = (ICMS+ISS) * 1.0 = 180 (só ICMS/ISS, não PIS/COFINS)
    # pis_cofins_residual = 0 porque cbs_substitui_pis_cofins=True (CBS já assumiu)
    assert resultado.carga_reforma == pytest.approx(100 + 0 + 180)


def test_2033_sistema_pleno_ibs_cbs_sem_residual(db):
    item = _item(1000, icms=180, pis=16.5, cofins=76)
    resultado = calcular_impacto_item(db, item, [2033])[0]

    # cbs = 100 ; ibs = 1000*0.20*1.0 = 200 ; residual = 0
    assert resultado.carga_reforma == pytest.approx(300.0)


def test_reducao_de_ncm_e_aplicada_sobre_cbs_ibs(db):
    item = _item(1000, ncm="10063021", icms=0, pis=0, cofins=0)  # NCM da cesta básica (100% redução)
    resultado = calcular_impacto_item(db, item, [2033])[0]

    assert resultado.percentual_reducao_aplicado == 1.0
    assert resultado.carga_reforma == pytest.approx(0.0)


def test_ano_sem_parametro_cadastrado_nao_inventa_numero(db):
    item = _item(1000, icms=180)
    resultado = calcular_impacto_item(db, item, [2099])[0]
    # Sem parâmetro para 2099: mantém a carga atual, não gera número fictício
    assert resultado.carga_reforma == resultado.carga_atual


def test_impacto_analise_agrega_todas_as_notas_e_marca_validacao(db):
    analise = models.Analise(nome_cliente="Cliente Teste")
    nota = models.NotaFiscal(nome_arquivo="a.xml", valor_total=1000)
    nota.itens = [_item(1000, icms=180, pis=16.5, cofins=76)]
    analise.notas = [nota]
    db.add(analise)
    db.commit()

    resultado = calcular_impacto_analise(db, analise, [2027, 2033])
    assert len(resultado) == 2
    assert all(r.parametros_validados for r in resultado)  # fixture marcou validado_por_tributarista=True
    assert resultado[0].ano == 2027
    assert resultado[1].ano == 2033
    assert resultado[1].carga_reforma > resultado[0].carga_reforma  # IBS pleno em 2033 pesa mais que 2027 nesse cenário
