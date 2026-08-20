import io
import zipfile

from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.parser.nfe_parser import parse_nfe_xml, NFeParseError

router = APIRouter()


def _arquivos_xml_de(nome: str, conteudo: bytes) -> list[tuple[str, bytes]]:
    """Se for .zip, extrai os .xml de dentro. Se for .xml, retorna direto.
    Nunca lança exceção -- zip corrompido também vira um erro reportado."""
    if nome.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
                return [
                    (info.filename, z.read(info.filename))
                    for info in z.infolist()
                    if info.filename.lower().endswith(".xml") and not info.is_dir()
                ]
        except zipfile.BadZipFile:
            return [(nome, b"")]  # cai no parser, que vai reportar XML inválido
    return [(nome, conteudo)]


@router.post("/api/analises", response_model=schemas.AnaliseResumoOut)
async def criar_analise(
    nome_cliente: str = Form(...),
    cnpj_cliente: str = Form(None),
    arquivos: list[UploadFile] = Form(...),
    db: Session = Depends(get_db),
):
    analise = models.Analise(nome_cliente=nome_cliente, cnpj_cliente=cnpj_cliente, status="processando")
    db.add(analise)
    db.flush()

    total_recebidas = 0
    total_processadas = 0
    total_com_erro = 0

    for upload in arquivos:
        conteudo = await upload.read()
        for nome_arquivo, xml_bytes in _arquivos_xml_de(upload.filename or "arquivo.xml", conteudo):
            total_recebidas += 1
            try:
                nota_parseada = parse_nfe_xml(xml_bytes)
            except NFeParseError as e:
                total_com_erro += 1
                db.add(models.ErroProcessamento(
                    analise_id=analise.id, nome_arquivo=nome_arquivo, motivo=str(e),
                ))
                continue

            nota = models.NotaFiscal(
                analise_id=analise.id,
                nome_arquivo=nome_arquivo,
                chave_acesso=nota_parseada.chave_acesso,
                numero=nota_parseada.numero,
                data_emissao=nota_parseada.data_emissao,
                cnpj_emitente=nota_parseada.cnpj_emitente,
                nome_emitente=nota_parseada.nome_emitente,
                valor_total=nota_parseada.valor_total,
            )
            db.add(nota)
            db.flush()

            for item in nota_parseada.itens:
                db.add(models.ItemNota(
                    nota_id=nota.id,
                    numero_item=item.numero_item,
                    codigo_produto=item.codigo_produto,
                    descricao_produto=item.descricao_produto,
                    ncm=item.ncm,
                    cfop=item.cfop,
                    valor_produto=item.valor_produto,
                    valor_icms=item.valor_icms,
                    valor_ipi=item.valor_ipi,
                    valor_pis=item.valor_pis,
                    valor_cofins=item.valor_cofins,
                    valor_issqn=item.valor_issqn,
                ))
            total_processadas += 1

    analise.total_notas_recebidas = total_recebidas
    analise.total_notas_processadas = total_processadas
    analise.total_notas_com_erro = total_com_erro
    analise.status = "concluida" if total_processadas > 0 else "erro"
    db.commit()
    db.refresh(analise)
    return analise
