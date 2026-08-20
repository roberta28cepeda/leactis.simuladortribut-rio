"""Parser de XML de NF-e (modelo 55), schema público da SEFAZ.

Não depende de nenhuma regra tributária da Reforma -- só extrai os campos
fiscais já destacados no XML (NCM, CFOP, valores, tributos do regime atual).
Por isso pode ser construído e testado antes de qualquer validação com
tributarista.

Usa local-name() nos XPaths em vez de namespace fixo, porque diferentes
emissores/versões variam ligeiramente a URI do namespace -- isso torna o
parser tolerante a essas variações sem precisar mapear cada uma.
"""

from dataclasses import dataclass, field
from typing import Optional

from lxml import etree


class NFeParseError(Exception):
    """XML corrompido, incompleto ou fora do schema esperado de NF-e."""


@dataclass
class ItemNFe:
    numero_item: int
    codigo_produto: Optional[str] = None
    descricao_produto: Optional[str] = None
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    valor_produto: float = 0.0
    valor_icms: float = 0.0
    valor_ipi: float = 0.0
    valor_pis: float = 0.0
    valor_cofins: float = 0.0
    valor_issqn: float = 0.0


@dataclass
class NotaFiscalParseada:
    chave_acesso: Optional[str] = None
    numero: Optional[str] = None
    data_emissao: Optional[str] = None
    cnpj_emitente: Optional[str] = None
    nome_emitente: Optional[str] = None
    valor_total: float = 0.0
    itens: list = field(default_factory=list)


def _xpath1(el, expr):
    r = el.xpath(expr)
    return r[0] if r else None


def _texto(el, expr, default=None):
    r = _xpath1(el, expr)
    if r is None:
        return default
    texto = r.text if hasattr(r, "text") else str(r)
    return texto.strip() if texto else default


def _numero(el, expr, default=0.0):
    texto = _texto(el, expr)
    if texto is None:
        return default
    try:
        return float(texto)
    except ValueError:
        return default


def _parse_item(det_el, numero_item: int) -> ItemNFe:
    prod = _xpath1(det_el, "./*[local-name()='prod']")
    imposto = _xpath1(det_el, "./*[local-name()='imposto']")

    item = ItemNFe(numero_item=numero_item)
    if prod is not None:
        item.codigo_produto = _texto(prod, "./*[local-name()='cProd']")
        item.descricao_produto = _texto(prod, "./*[local-name()='xProd']")
        item.ncm = _texto(prod, "./*[local-name()='NCM']")
        item.cfop = _texto(prod, "./*[local-name()='CFOP']")
        item.valor_produto = _numero(prod, "./*[local-name()='vProd']")

    if imposto is not None:
        # ICMS: o filho varia (ICMS00, ICMS10, ICMS20, ICMS40, ICMS51,
        # ICMS60, ICMS70, ICMS90, ICMSSN...) conforme o CST/CSOSN -- pega
        # o valor de dentro de qualquer que seja o grupo presente.
        icms_grupo = _xpath1(imposto, "./*[local-name()='ICMS']/*[1]")
        if icms_grupo is not None:
            item.valor_icms = _numero(icms_grupo, "./*[local-name()='vICMS']")

        ipi_grupo = _xpath1(imposto, "./*[local-name()='IPI']/*[local-name()='IPITrib']")
        if ipi_grupo is not None:
            item.valor_ipi = _numero(ipi_grupo, "./*[local-name()='vIPI']")

        pis_grupo = _xpath1(imposto, "./*[local-name()='PIS']/*[1]")
        if pis_grupo is not None:
            item.valor_pis = _numero(pis_grupo, "./*[local-name()='vPIS']")

        cofins_grupo = _xpath1(imposto, "./*[local-name()='COFINS']/*[1]")
        if cofins_grupo is not None:
            item.valor_cofins = _numero(cofins_grupo, "./*[local-name()='vCOFINS']")

        issqn_grupo = _xpath1(imposto, "./*[local-name()='ISSQN']")
        if issqn_grupo is not None:
            item.valor_issqn = _numero(issqn_grupo, "./*[local-name()='vISSQN']")

    return item


def parse_nfe_xml(conteudo_xml: bytes) -> NotaFiscalParseada:
    """Recebe os bytes de um arquivo XML de NF-e e retorna os campos
    estruturados. Levanta NFeParseError com mensagem clara se o arquivo
    não for um XML válido ou não tiver a estrutura mínima de NF-e."""
    try:
        root = etree.fromstring(conteudo_xml)
    except etree.XMLSyntaxError as e:
        raise NFeParseError(f"XML inválido ou corrompido: {e}") from e

    inf_nfe = _xpath1(root, "//*[local-name()='infNFe']")
    if inf_nfe is None:
        raise NFeParseError(
            "Não encontrei a tag <infNFe> -- este arquivo não parece ser "
            "uma NF-e (modelo 55) no schema esperado."
        )

    ide = _xpath1(inf_nfe, "./*[local-name()='ide']")
    emit = _xpath1(inf_nfe, "./*[local-name()='emit']")
    total = _xpath1(inf_nfe, "./*[local-name()='total']/*[local-name()='ICMSTot']")
    dets = inf_nfe.xpath("./*[local-name()='det']")

    if not dets:
        raise NFeParseError(
            "A NF-e não tem nenhum item (<det>) -- arquivo incompleto."
        )

    nota = NotaFiscalParseada()
    nota.chave_acesso = _xpath1(inf_nfe, "@Id")
    if nota.chave_acesso:
        nota.chave_acesso = nota.chave_acesso.replace("NFe", "")

    if ide is not None:
        nota.numero = _texto(ide, "./*[local-name()='nNF']")
        nota.data_emissao = _texto(ide, "./*[local-name()='dhEmi']") or _texto(ide, "./*[local-name()='dEmi']")

    if emit is not None:
        nota.cnpj_emitente = _texto(emit, "./*[local-name()='CNPJ']")
        nota.nome_emitente = _texto(emit, "./*[local-name()='xNome']")

    if total is not None:
        nota.valor_total = _numero(total, "./*[local-name()='vNF']")

    for i, det in enumerate(dets, start=1):
        nota.itens.append(_parse_item(det, i))

    return nota
