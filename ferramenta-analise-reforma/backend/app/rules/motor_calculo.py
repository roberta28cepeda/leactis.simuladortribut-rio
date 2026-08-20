"""Motor de cálculo do impacto da Reforma Tributária.

Regime atual x reforma, ano a ano, item a item.

TUDO aqui é parametrizável: nenhuma alíquota, percentual de transição ou
redução de NCM fica fixa no código -- tudo vem das tabelas de parâmetros
(ver app/models.py: ParametroAliquotaReferencia, ParametroTransicaoAno,
ParametroReducaoNcm). Isso é proposital, porque essas regras vêm sendo
publicadas em fases pelo Comitê Gestor do IBS/Receita Federal e vão mudar
por decreto ao longo dos anos até 2033.

⚠️ Os parâmetros seedados em seed_parametros.py são PLACEHOLDERS
ilustrativos, com `validado_por_tributarista=False`. Este motor calcula
corretamente EM CIMA dos parâmetros que você der a ele -- mas não garante
que os parâmetros atuais reflitam a lei. Ver README.md.
"""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app import models


@dataclass
class ImpactoItemAno:
    ano: int
    carga_atual: float
    carga_reforma: float
    percentual_reducao_aplicado: float


@dataclass
class ImpactoAno:
    ano: int
    carga_atual: float
    carga_reforma: float
    diferenca: float
    parametros_validados: bool  # False se algum parâmetro usado ainda não foi validado por tributarista


def carga_tributaria_atual(item: "models.ItemNota") -> float:
    """Soma os tributos já destacados no XML da nota (regime vigente)."""
    return (
        (item.valor_icms or 0.0)
        + (item.valor_ipi or 0.0)
        + (item.valor_pis or 0.0)
        + (item.valor_cofins or 0.0)
        + (item.valor_issqn or 0.0)
    )


def _percentual_reducao_ncm(db: Session, ncm: Optional[str]) -> tuple[float, bool]:
    """Retorna (percentual_reducao, algum_parametro_encontrado). Usa o
    prefixo de NCM mais específico cadastrado; se nenhum bater, assume 0%
    de redução (alíquota cheia)."""
    if not ncm:
        return 0.0, True  # sem NCM não há o que reduzir; não é motivo de alerta

    regras = db.query(models.ParametroReducaoNcm).all()
    melhor = None
    for regra in regras:
        if ncm.startswith(regra.ncm_prefixo) and (melhor is None or len(regra.ncm_prefixo) > len(melhor.ncm_prefixo)):
            melhor = regra

    if melhor is None:
        return 0.0, True

    return melhor.percentual_reducao, melhor.validado_por_tributarista


def calcular_impacto_item(
    db: Session, item: "models.ItemNota", anos: list[int]
) -> list[ImpactoItemAno]:
    carga_atual = carga_tributaria_atual(item)
    reducao_ncm, ncm_validado = _percentual_reducao_ncm(db, item.ncm)

    aliquotas_por_ano = {
        p.ano: p for p in db.query(models.ParametroAliquotaReferencia).all()
    }
    transicao_por_ano = {
        p.ano: p for p in db.query(models.ParametroTransicaoAno).all()
    }

    resultados = []
    for ano in anos:
        aliquota = aliquotas_por_ano.get(ano)
        transicao = transicao_por_ano.get(ano)
        if aliquota is None or transicao is None:
            # Sem parâmetro cadastrado pra esse ano: não inventa número,
            # reporta a carga atual como se nada mudasse (sinal claro de
            # que falta configurar esse ano).
            resultados.append(ImpactoItemAno(
                ano=ano, carga_atual=carga_atual, carga_reforma=carga_atual,
                percentual_reducao_aplicado=0.0,
            ))
            continue

        base = item.valor_produto or 0.0
        cbs = base * aliquota.cbs_referencia if transicao.cbs_substitui_pis_cofins else 0.0
        ibs = base * aliquota.ibs_referencia * transicao.fracao_ibs_ativa

        # Cada tributo antigo só é "residual" dentro do seu próprio grupo --
        # nunca sobre a carga_atual inteira (isso duplicaria PIS/COFINS
        # junto com o resíduo de ICMS/ISS). IPI não é tocado pela transição
        # neste placeholder (simplificação: a reforma não extingue o IPI
        # diretamente, ver README.md).
        icms_iss_atual = (item.valor_icms or 0.0) + (item.valor_issqn or 0.0)
        pis_cofins_atual = (item.valor_pis or 0.0) + (item.valor_cofins or 0.0)
        ipi_atual = item.valor_ipi or 0.0

        icms_iss_residual = icms_iss_atual * transicao.fracao_icms_iss_residual
        pis_cofins_residual = 0.0 if transicao.cbs_substitui_pis_cofins else pis_cofins_atual

        carga_reforma_bruta = (cbs + ibs) * (1 - reducao_ncm) + icms_iss_residual + pis_cofins_residual + ipi_atual

        resultados.append(ImpactoItemAno(
            ano=ano,
            carga_atual=carga_atual,
            carga_reforma=round(carga_reforma_bruta, 2),
            percentual_reducao_aplicado=reducao_ncm,
        ))

    return resultados


def calcular_impacto_analise(db: Session, analise: "models.Analise", anos: list[int]) -> list[ImpactoAno]:
    """Agrega o impacto de todos os itens de todas as notas de uma análise,
    ano a ano."""
    todos_parametros_validados = _todos_parametros_validados(db, anos)

    acumulado = {ano: {"atual": 0.0, "reforma": 0.0} for ano in anos}
    for nota in analise.notas:
        for item in nota.itens:
            for r in calcular_impacto_item(db, item, anos):
                acumulado[r.ano]["atual"] += r.carga_atual
                acumulado[r.ano]["reforma"] += r.carga_reforma

    return [
        ImpactoAno(
            ano=ano,
            carga_atual=round(acumulado[ano]["atual"], 2),
            carga_reforma=round(acumulado[ano]["reforma"], 2),
            diferenca=round(acumulado[ano]["reforma"] - acumulado[ano]["atual"], 2),
            parametros_validados=todos_parametros_validados,
        )
        for ano in anos
    ]


def _todos_parametros_validados(db: Session, anos: list[int]) -> bool:
    aliquotas = db.query(models.ParametroAliquotaReferencia).filter(
        models.ParametroAliquotaReferencia.ano.in_(anos)
    ).all()
    transicoes = db.query(models.ParametroTransicaoAno).filter(
        models.ParametroTransicaoAno.ano.in_(anos)
    ).all()
    if len(aliquotas) < len(anos) or len(transicoes) < len(anos):
        return False
    return all(p.validado_por_tributarista for p in aliquotas) and all(p.validado_por_tributarista for p in transicoes)
