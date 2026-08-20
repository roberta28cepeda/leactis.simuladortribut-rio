# Leactis — Análise de Impacto da Reforma Tributária

> Esta pasta é um projeto separado dentro deste repositório: um sistema
> B2B para escritórios de contabilidade, sem relação com a landing page de
> anúncio pago que vive na raiz do repositório (`/index.html`,
> `simulador.leactis.com.br`). Deploy, banco de dados e domínio são
> independentes — ver instruções abaixo.

MVP técnico da ferramenta descrita no PRD (upload de XML de NF-e → comparação
da carga tributária atual x Reforma Tributária, ano a ano, 2026–2033),
para escritórios de contabilidade.

## ⚠️ Status: base técnica, sem validação tributária ainda

Este projeto implementa a **arquitetura completa** do MVP P0 do PRD (parser
de XML, motor de cálculo parametrizável, API, tela de resultado, exportação
em PDF) e está **testado de ponta a ponta** — mas os **valores tributários
usados no cálculo são placeholders ilustrativos**, não validados por um
tributarista. Isso é proposital: o próprio PRD e o plano de validação
recomendam não travar nenhuma regra tributária no código antes de validar
com especialista e com os 5–10 escritórios-piloto.

Todo parâmetro tributário (alíquota de referência de CBS/IBS, cronograma de
transição, reduções por NCM) tem uma flag `validado_por_tributarista` no
banco — enquanto ela for `False`, a API e a tela de resultado exibem um
aviso explícito. **Não apresente os números gerados hoje a um cliente
real.**

Ver `roteiro-entrevistas-validacao.md` (enviado à parte) para o roteiro de
validação com os escritórios-piloto — os resultados dessa validação são o
que deve preencher a tabela de parâmetros de verdade.

## O que já funciona (testado)

- **Parser de XML de NF-e** (modelo 55, schema público SEFAZ): extrai NCM,
  CFOP, valores e tributos (ICMS, IPI, PIS, COFINS, ISSQN) de cada item.
  Tolerante a variações de namespace entre emissores. 6 testes cobrindo nota
  válida, item isento e 3 tipos de arquivo corrompido/incompleto.
- **Motor de cálculo parametrizável**: dado os parâmetros tributários de um
  ano, calcula a carga atual x carga com a reforma por item, agregando por
  análise. 6 testes cobrindo os cenários de início e fim da transição,
  redução por NCM, e ano sem parâmetro cadastrado (não inventa número).
- **API REST (FastAPI)**: upload de XML/`.zip` em lote, cálculo do impacto
  ano a ano, listagem/detalhe de análises, exportação em PDF. Upload com
  arquivo corrompido não trava o processamento dos demais — cada erro é
  reportado individualmente (requisito P0 do PRD). 5 testes de integração
  cobrindo o fluxo completo.
- **Frontend (React + Vite + recharts)**: tela de upload e tela de
  resultado com gráfico comparativo, tabela ano a ano, lista de erros de
  leitura e botão de exportar PDF.
- **17 testes automatizados, todos passando** (`pytest`).

## O que ainda não está aqui (fora do escopo desta rodada)

Seguindo o PRD: leitura de SPED, módulo de crédito tributário,
precificação/margem, efeito caixa/Split Payment, multi-cliente,
integração e-CAC, autenticação de usuários. Tudo isso é Fase 2+ no PRD.

---

## Rodando localmente

### Opção 1 — Docker (mais simples)

```bash
docker compose up --build
```
Backend sobe em `http://localhost:8000`, já com Postgres e os parâmetros
placeholder semeados automaticamente.

Frontend (fora do compose, por enquanto):
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### Opção 2 — Manual (sem Docker)

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed_parametros   # popula parâmetros placeholder (SQLite por padrão)
uvicorn app.main:app --reload

# Frontend (outro terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Abra `http://localhost:5173`, suba o XML de exemplo em
`backend/tests/fixtures/nfe_exemplo.xml` pra ver o fluxo funcionando.

Por padrão o backend usa SQLite (`backend/leactis_reforma.db`, zero setup).
Para usar PostgreSQL (recomendado para produção), defina `DATABASE_URL`:
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/leactis_reforma
```

### Rodando os testes

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

---

## Como validar/atualizar os parâmetros tributários

Depois que a validação com o tributarista e os escritórios-piloto estiver
pronta, atualize `backend/app/seed_parametros.py` com os valores reais
(ou insira direto nas tabelas `parametros_aliquota_referencia`,
`parametros_transicao_ano` e `parametros_reducao_ncm` via banco), e marque
`validado_por_tributarista=True` com a fonte legal em `fonte` (ex: "LC
214/2025, art. X"). O motor de cálculo já lê essas tabelas em tempo de
execução — nenhuma mudança de código é necessária para atualizar alíquotas
ou o cronograma de transição.

## Estrutura

```
backend/
  app/
    parser/nfe_parser.py       parser de XML de NF-e (não depende de regra tributária)
    rules/motor_calculo.py     motor de cálculo parametrizável
    models.py                  ORM (notas, itens, parâmetros tributários)
    api/                       endpoints (upload, análises, PDF)
    seed_parametros.py         popula parâmetros PLACEHOLDER
  tests/                       17 testes (parser, motor de cálculo, API)
frontend/
  src/App.jsx                  tela de upload + tela de resultado
docker-compose.yml
```
