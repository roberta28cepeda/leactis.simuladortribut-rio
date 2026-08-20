import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, Text, Boolean,
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Analise(Base):
    """Uma análise = um lote de XMLs de um cliente, processado de uma vez."""
    __tablename__ = "analises"

    id = Column(String, primary_key=True, default=gen_uuid)
    nome_cliente = Column(String, nullable=False)
    cnpj_cliente = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processando")  # processando | concluida | erro
    total_notas_recebidas = Column(Integer, default=0)
    total_notas_processadas = Column(Integer, default=0)
    total_notas_com_erro = Column(Integer, default=0)

    notas = relationship("NotaFiscal", back_populates="analise", cascade="all, delete-orphan")
    erros = relationship("ErroProcessamento", back_populates="analise", cascade="all, delete-orphan")


class ErroProcessamento(Base):
    """Registra cada XML que não pôde ser processado, e por quê -- P0 do PRD:
    'tratamento de erro de upload: XML inválido, corrompido ou de schema
    incompatível gera mensagem clara, não trava o sistema'."""
    __tablename__ = "erros_processamento"

    id = Column(String, primary_key=True, default=gen_uuid)
    analise_id = Column(String, ForeignKey("analises.id"), nullable=False)
    nome_arquivo = Column(String, nullable=False)
    motivo = Column(Text, nullable=False)

    analise = relationship("Analise", back_populates="erros")


class NotaFiscal(Base):
    __tablename__ = "notas_fiscais"

    id = Column(String, primary_key=True, default=gen_uuid)
    analise_id = Column(String, ForeignKey("analises.id"), nullable=False)
    nome_arquivo = Column(String, nullable=False)
    chave_acesso = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    data_emissao = Column(String, nullable=True)
    cnpj_emitente = Column(String, nullable=True)
    nome_emitente = Column(String, nullable=True)
    valor_total = Column(Float, default=0.0)

    analise = relationship("Analise", back_populates="notas")
    itens = relationship("ItemNota", back_populates="nota", cascade="all, delete-orphan")


class ItemNota(Base):
    """Um item (linha de produto) de uma NF-e, com os tributos atuais
    destacados no XML e o NCM/CFOP usados pelo motor de cálculo."""
    __tablename__ = "itens_nota"

    id = Column(String, primary_key=True, default=gen_uuid)
    nota_id = Column(String, ForeignKey("notas_fiscais.id"), nullable=False)

    numero_item = Column(Integer, nullable=False)
    codigo_produto = Column(String, nullable=True)
    descricao_produto = Column(String, nullable=True)
    ncm = Column(String, nullable=True)
    cfop = Column(String, nullable=True)
    valor_produto = Column(Float, default=0.0)

    # Tributos atuais destacados no XML (regime vigente)
    valor_icms = Column(Float, default=0.0)
    valor_ipi = Column(Float, default=0.0)
    valor_pis = Column(Float, default=0.0)
    valor_cofins = Column(Float, default=0.0)
    valor_issqn = Column(Float, default=0.0)

    nota = relationship("NotaFiscal", back_populates="itens")


# ---------------------------------------------------------------------------
# Motor de regras PARAMETRIZÁVEL. Nenhuma alíquota fica fixa no código -- tudo
# aqui é lido destas tabelas em tempo de execução, exatamente pra suportar
# mudanças normativas ao longo da transição (2026-2033) sem reescrever nada.
#
# ATENÇÃO: os valores seedados em seed_parametros.py são PLACEHOLDERS
# ilustrativos para permitir testar a arquitetura de ponta a ponta. NENHUM
# valor aqui foi validado por um tributarista. Ver README.md.
# ---------------------------------------------------------------------------

class ParametroAliquotaReferencia(Base):
    """Alíquota de referência de CBS/IBS por ano (CBS_REF, IBS_REF)."""
    __tablename__ = "parametros_aliquota_referencia"

    id = Column(String, primary_key=True, default=gen_uuid)
    ano = Column(Integer, nullable=False, unique=True)
    cbs_referencia = Column(Float, nullable=False)
    ibs_referencia = Column(Float, nullable=False)
    validado_por_tributarista = Column(Boolean, default=False)
    fonte = Column(String, nullable=True)  # ex: "LC 214/2025, art. X" -- preencher na validação


class ParametroTransicaoAno(Base):
    """Cronograma de transição: qual fração do IBS já está ativa e qual
    fração do ICMS/ISS antigo ainda é cobrada, por ano."""
    __tablename__ = "parametros_transicao_ano"

    id = Column(String, primary_key=True, default=gen_uuid)
    ano = Column(Integer, nullable=False, unique=True)
    fracao_ibs_ativa = Column(Float, nullable=False)       # 0.0 a 1.0
    fracao_icms_iss_residual = Column(Float, nullable=False)  # 0.0 a 1.0
    cbs_substitui_pis_cofins = Column(Boolean, default=True)
    validado_por_tributarista = Column(Boolean, default=False)
    fonte = Column(String, nullable=True)


class ParametroReducaoNcm(Base):
    """Reduções/isenções por NCM (ex: cesta básica = redução de 100%,
    certos itens = redução de 60%). Prefixo de NCM permite regras por
    categoria sem cadastrar cada NCM individualmente."""
    __tablename__ = "parametros_reducao_ncm"

    id = Column(String, primary_key=True, default=gen_uuid)
    ncm_prefixo = Column(String, nullable=False)  # ex: "1006" (arroz)
    percentual_reducao = Column(Float, nullable=False)  # 0.0 a 1.0
    descricao = Column(String, nullable=True)
    validado_por_tributarista = Column(Boolean, default=False)
    fonte = Column(String, nullable=True)
