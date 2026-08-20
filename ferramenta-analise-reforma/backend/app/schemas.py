from typing import Optional

from pydantic import BaseModel, ConfigDict


class ErroProcessamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome_arquivo: str
    motivo: str


class ImpactoAnoOut(BaseModel):
    ano: int
    carga_atual: float
    carga_reforma: float
    diferenca: float
    parametros_validados: bool


class AnaliseResumoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome_cliente: str
    cnpj_cliente: Optional[str]
    status: str
    total_notas_recebidas: int
    total_notas_processadas: int
    total_notas_com_erro: int


class AnaliseDetalheOut(AnaliseResumoOut):
    erros: list[ErroProcessamentoOut]
    impacto_por_ano: list[ImpactoAnoOut]
    aviso_parametros_nao_validados: Optional[str] = None
