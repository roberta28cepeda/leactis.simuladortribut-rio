from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.rules.motor_calculo import calcular_impacto_analise

ANOS_ANALISE = list(range(2026, 2034))

router = APIRouter()


def _montar_detalhe(db: Session, analise: models.Analise) -> schemas.AnaliseDetalheOut:
    impacto = calcular_impacto_analise(db, analise, ANOS_ANALISE)
    aviso = None
    if impacto and not all(i.parametros_validados for i in impacto):
        aviso = (
            "Um ou mais parâmetros usados neste cálculo (alíquotas de referência, "
            "cronograma de transição ou reduções de NCM) ainda não foram validados "
            "por um tributarista. Trate estes números como estimativa preliminar."
        )
    return schemas.AnaliseDetalheOut(
        id=analise.id,
        nome_cliente=analise.nome_cliente,
        cnpj_cliente=analise.cnpj_cliente,
        status=analise.status,
        total_notas_recebidas=analise.total_notas_recebidas,
        total_notas_processadas=analise.total_notas_processadas,
        total_notas_com_erro=analise.total_notas_com_erro,
        erros=[schemas.ErroProcessamentoOut.model_validate(e) for e in analise.erros],
        impacto_por_ano=[schemas.ImpactoAnoOut(**vars(i)) for i in impacto],
        aviso_parametros_nao_validados=aviso,
    )


@router.get("/api/analises", response_model=list[schemas.AnaliseResumoOut])
def listar_analises(db: Session = Depends(get_db)):
    return db.query(models.Analise).order_by(models.Analise.criado_em.desc()).all()


@router.get("/api/analises/{analise_id}", response_model=schemas.AnaliseDetalheOut)
def obter_analise(analise_id: str, db: Session = Depends(get_db)):
    analise = db.query(models.Analise).filter(models.Analise.id == analise_id).first()
    if analise is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return _montar_detalhe(db, analise)
