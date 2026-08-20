import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seed_parametros import seed as seed_placeholder_parametros

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # popula os parâmetros placeholder nesse mesmo banco de teste
    monkeypatch.setattr("app.seed_parametros.engine", engine)
    monkeypatch.setattr("app.seed_parametros.SessionLocal", TestingSession)
    seed_placeholder_parametros()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_upload_analise_e_calcula_impacto(client):
    with open(os.path.join(FIXTURES, "nfe_exemplo.xml"), "rb") as f:
        r = client.post(
            "/api/analises",
            data={"nome_cliente": "Empresa Teste LTDA", "cnpj_cliente": "98765432000188"},
            files=[("arquivos", ("nfe_exemplo.xml", f, "application/xml"))],
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "concluida"
    assert body["total_notas_processadas"] == 1
    assert body["total_notas_com_erro"] == 0

    analise_id = body["id"]
    r2 = client.get(f"/api/analises/{analise_id}")
    assert r2.status_code == 200
    detalhe = r2.json()
    assert len(detalhe["impacto_por_ano"]) == 8  # 2026-2033
    assert detalhe["aviso_parametros_nao_validados"] is not None  # seed é placeholder, deve avisar
    # todo ano deve ter algum valor de carga (não travou em zero por falta de parâmetro)
    assert all(i["carga_atual"] > 0 for i in detalhe["impacto_por_ano"])


def test_upload_arquivo_invalido_nao_trava_e_reporta_erro(client):
    r = client.post(
        "/api/analises",
        data={"nome_cliente": "Empresa Teste LTDA"},
        files=[("arquivos", ("quebrado.xml", b"isso nao e xml", "application/xml"))],
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "erro"
    assert body["total_notas_com_erro"] == 1
    assert body["total_notas_processadas"] == 0

    r2 = client.get(f"/api/analises/{body['id']}")
    assert len(r2.json()["erros"]) == 1
    assert "quebrado.xml" == r2.json()["erros"][0]["nome_arquivo"]


def test_exporta_pdf(client):
    with open(os.path.join(FIXTURES, "nfe_exemplo.xml"), "rb") as f:
        r = client.post(
            "/api/analises",
            data={"nome_cliente": "Empresa Teste LTDA"},
            files=[("arquivos", ("nfe_exemplo.xml", f, "application/xml"))],
        )
    analise_id = r.json()["id"]

    r2 = client.get(f"/api/analises/{analise_id}/pdf")
    assert r2.status_code == 200
    assert r2.headers["content-type"] == "application/pdf"
    assert r2.content[:4] == b"%PDF"


def test_analise_inexistente_retorna_404(client):
    r = client.get("/api/analises/nao-existe")
    assert r.status_code == 404
