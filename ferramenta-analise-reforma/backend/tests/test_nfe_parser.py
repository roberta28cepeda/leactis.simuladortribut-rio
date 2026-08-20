import os

import pytest

from app.parser.nfe_parser import parse_nfe_xml, NFeParseError

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _ler_fixture(nome):
    with open(os.path.join(FIXTURES, nome), "rb") as f:
        return f.read()


def test_parseia_nota_valida():
    nota = parse_nfe_xml(_ler_fixture("nfe_exemplo.xml"))

    assert nota.numero == "1234"
    assert nota.cnpj_emitente == "12345678000199"
    assert nota.nome_emitente == "Fornecedor Exemplo LTDA"
    assert nota.valor_total == 1200.00
    assert len(nota.itens) == 2


def test_item_tributado_normalmente():
    nota = parse_nfe_xml(_ler_fixture("nfe_exemplo.xml"))
    item1 = nota.itens[0]

    assert item1.ncm == "84713012"
    assert item1.cfop == "5102"
    assert item1.valor_produto == 1000.00
    assert item1.valor_icms == 180.00
    assert item1.valor_pis == 16.50
    assert item1.valor_cofins == 76.00


def test_item_isento_sem_valores_de_tributo():
    nota = parse_nfe_xml(_ler_fixture("nfe_exemplo.xml"))
    item2 = nota.itens[1]

    assert item2.ncm == "10063021"
    assert item2.valor_produto == 200.00
    # ICMS40/PISNT/COFINSNT não têm vICMS/vPIS/vCOFINS -- deve ficar 0, não erro
    assert item2.valor_icms == 0.0
    assert item2.valor_pis == 0.0
    assert item2.valor_cofins == 0.0


def test_xml_corrompido_gera_erro_claro():
    with pytest.raises(NFeParseError, match="corrompido"):
        parse_nfe_xml(b"isso nao e um xml valido <<<")


def test_xml_sem_infnfe_gera_erro_claro():
    with pytest.raises(NFeParseError, match="infNFe"):
        parse_nfe_xml(b"<algumaOutraCoisa><foo>bar</foo></algumaOutraCoisa>")


def test_nfe_sem_itens_gera_erro_claro():
    xml_sem_det = b"""<?xml version="1.0"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
      <NFe><infNFe Id="NFe123"><ide><nNF>1</nNF></ide></infNFe></NFe>
    </nfeProc>"""
    with pytest.raises(NFeParseError, match="nenhum item"):
        parse_nfe_xml(xml_sem_det)
