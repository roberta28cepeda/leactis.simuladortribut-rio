import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.api.analises import _montar_detalhe

router = APIRouter()


def _fmt_moeda(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@router.get("/api/analises/{analise_id}/pdf")
def exportar_pdf(analise_id: str, db: Session = Depends(get_db)):
    analise = db.query(models.Analise).filter(models.Analise.id == analise_id).first()
    if analise is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    detalhe = _montar_detalhe(db, analise)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Análise de Impacto da Reforma Tributária", styles["Title"]))
    elementos.append(Paragraph(f"Cliente: {detalhe.nome_cliente}", styles["Normal"]))
    if detalhe.cnpj_cliente:
        elementos.append(Paragraph(f"CNPJ: {detalhe.cnpj_cliente}", styles["Normal"]))
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph(
        f"Notas processadas: {detalhe.total_notas_processadas} de {detalhe.total_notas_recebidas} "
        f"recebidas ({detalhe.total_notas_com_erro} com erro de leitura).",
        styles["Normal"],
    ))
    elementos.append(Spacer(1, 0.8 * cm))

    dados_tabela = [["Ano", "Carga atual", "Carga com a reforma", "Diferença"]]
    for i in detalhe.impacto_por_ano:
        dados_tabela.append([str(i.ano), _fmt_moeda(i.carga_atual), _fmt_moeda(i.carga_reforma), _fmt_moeda(i.diferenca)])

    tabela = Table(dados_tabela, hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2341")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F3")]),
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 1 * cm))

    if detalhe.aviso_parametros_nao_validados:
        elementos.append(Paragraph(f"⚠️ {detalhe.aviso_parametros_nao_validados}", styles["Normal"]))
        elementos.append(Spacer(1, 0.5 * cm))

    elementos.append(Paragraph(
        "Esta é uma análise simulada, gerada automaticamente a partir dos XMLs de NF-e "
        "informados. Não substitui parecer técnico assinado por contador ou tributarista "
        "responsável.",
        styles["Italic"],
    ))

    doc.build(elementos)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="analise-{analise_id[:8]}.pdf"'},
    )
