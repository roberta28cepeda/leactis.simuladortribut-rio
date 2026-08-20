from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analises, pdf, upload
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Leactis — Análise de Impacto da Reforma Tributária",
    description=(
        "MVP para escritórios de contabilidade. ⚠️ Os parâmetros tributários "
        "usados no cálculo são placeholders não validados por um tributarista "
        "-- ver README.md antes de usar com clientes reais."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP local; restrinja em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(analises.router)
app.include_router(pdf.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
