# Especificação Técnica — Motor de Cálculo IBS/CBS

**Status:** Rascunho v1 — REQUER VALIDAÇÃO DE TRIBUTARISTA antes de implementação
**Base legal:** LC 214/2025, LC 227/2026 (governança/contencioso), EC 132/2023
**Escopo:** Regras de transição e alíquotas ano a ano (2026–2033) para o motor de cálculo do MVP

---

## ⚠️ Aviso importante

Este documento consolida informações de fontes secundárias (artigos e escritórios de contabilidade) sobre a LC 214/2025, já que a regulamentação complementar segue sendo publicada em fases pelo Comitê Gestor do IBS (CGIBS) e pela Receita Federal. **Antes de codificar qualquer alíquota ou regra**, valide:

1. O texto oficial da LC 214/2025 e LC 227/2026 (Planalto)
2. Atos normativos complementares mais recentes do CGIBS
3. Um tributarista de referência, revisando cada ano do cronograma

O motor de cálculo **deve** ser parametrizável (alíquotas e regras em tabela/config, não hardcoded), porque esses valores podem mudar por resolução do Senado e atos do CGIBS ao longo dos anos.

---

## 1. Visão geral do cronograma de transição

| Período | O que muda |
|---|---|
| **2026** | Ano de teste. IBS e CBS incidem em alíquotas simbólicas, com neutralidade de carga (compensação com sistema atual). Sem impacto arrecadatório real. |
| **2027–2028** | CBS entra em vigor integral (substitui PIS/COFINS). IBS segue em alíquota reduzida, mas com arrecadação efetiva (não mais neutralizada). Imposto Seletivo (IS) começa a incidir. IPI passa a zero (exceto Zona Franca de Manaus). |
| **2029–2032** | Transição gradual: ICMS e ISS são reduzidos progressivamente enquanto o IBS assume a fatia correspondente, em proporções anuais crescentes. |
| **2033** | Sistema pleno: ICMS, ISS, PIS e COFINS extintos. Only IBS + CBS + IS em regime consolidado. |

---

## 2. Alíquotas de referência (a validar)

Segundo as fontes consultadas, a alíquota nominal combinada de referência no regime pleno (2033) é de aproximadamente:

- **CBS (federal):** ~8,8%
- **IBS (estadual + municipal):** ~17,7%
- **Total combinado:** ~26,5%

Esses são valores de referência amplamente citados, mas a alíquota efetiva final está sujeita a cálculo anual pelo Senado Federal, conforme trava constitucional de carga tributária. **O motor deve tratar a alíquota de referência como parâmetro atualizável, não como constante.**

### 2026 — Fase de teste
- CBS: 0,9%
- IBS: 0,1% (estadual, com posterior divisão)
- Compensável com PIS/COFINS e ICMS/ISS pagos no mesmo período — carga efetiva neutralizada
- Empresa que cumprir obrigações acessórias corretamente pode ficar dispensada do recolhimento efetivo
- Simples Nacional e MEI: não sujeitos às alíquotas de transição em 2026 (sem alteração prática)

### 2027–2028
- CBS: alíquota cheia (substitui PIS/COFINS integralmente)
- IBS: alíquota total permanece baixa (referência ~0,1%), mas repartida entre estadual e municipal (ex.: 0,05% + 0,05%, conforme art. 344), já com arrecadação efetiva (fim da neutralidade)
- Imposto Seletivo (IS) começa a incidir sobre itens específicos (combustíveis fósseis, bebidas açucaradas, cigarros, produtos poluentes)
- IPI reduzido a zero, exceto para produtos da Zona Franca de Manaus

### 2029–2032 — CONFIRMADO (múltiplas fontes convergem, incluindo Receita Federal)

Base legal: **art. 128 e art. 129, II, do ADCT** (incluídos pela EC 132/2023).

| Ano | ICMS + ISS (fração da alíquota original) | IBS (participação na nova tributação) |
|---|---|---|
| 2029 | 9/10 (90%) | 10% |
| 2030 | 8/10 (80%) | 20% |
| 2031 | 7/10 (70%) | 30% |
| 2032 | 6/10 (60%) | 40% |
| 2033 | 0% (extinto) | 100% |

**Regra de cálculo (importante, fonte de erro comum):** a redução é aplicada sobre a **alíquota original vigente em 2028** (a "base de comparação" fica fixa), não sobre o valor do ano anterior. Ou seja, o cálculo é multiplicativo a partir da alíquota de origem em cada ano, não um desconto acumulado ano a ano.

```
Carga_ICMS_ISS(ano) = Aliquota_original_2028 × Fracao(ano)
onde Fracao(2029)=0,9 | Fracao(2030)=0,8 | Fracao(2031)=0,7 | Fracao(2032)=0,6 | Fracao(2033+)=0
```

Exemplo (ICMS nominal de 17%):
- 2029: 17% × 0,9 = 15,3%
- 2030: 17% × 0,8 = 13,6%
- 2031: 17% × 0,7 = 11,9%
- 2032: 17% × 0,6 = 10,2%
- 2033: 0%

**Isso é crítico para o motor de cálculo**: se implementado errado como subtração de pontos percentuais fixos por ano (em vez de multiplicação pela fração sobre a base original), o resultado diverge — principalmente em alíquotas não múltiplas de 10 ou em cargas efetivas com casas decimais (comum após reduções de base de cálculo).

**Benefícios fiscais de ICMS** (incentivos estaduais, ex.: guerra fiscal) seguem a mesma proporção de redução (90%/80%/70%/60%) e são extintos em 2033, conforme art. 128, §1º do ADCT combinado com a LC 214/2025 (que alterou a regra de redução anual de incentivos, antes prevista na LC 160/2017, para acompanhar este mesmo cronograma).

**Trava de referência / possível ajuste**: a alíquota de referência do IBS/CBS pode ser recalibrada pelo Senado Federal (art. 130, §§4º-5º do ADCT) caso a arrecadação exceda o teto de referência — em 2030 (revisão da CBS) e em 2035 (revisão de CBS+IBS, com base na média de 2029–2033). O motor deve tratar isso como evento futuro possível, não como certeza — mas o cronograma de substituição ICMS/ISS→IBS acima (90/80/70/60/0) está na Constituição (ADCT) e não depende dessa calibragem.

### 2033 em diante
- Sistema pleno: ICMS, ISS, PIS, COFINS extintos
- Cobrança apenas de IBS + CBS + IS

---

## 3. Regras especiais que o motor precisa suportar

- **Regimes diferenciados / alíquota reduzida**: setores essenciais (ex.: cesta básica com alíquota zero, saúde, educação) têm percentual de redução sobre a alíquota de referência — depende de lista positiva por NCM/CNAE definida em lei complementar
- **Simples Nacional**: tratamento diferenciado
  - 2026: sem alteração prática
  - A partir de 2027: passa a destacar IBS/CBS nos documentos fiscais
  - Empresas do Simples podem optar por participar do sistema de créditos de IBS/CBS (vantajoso se tiver muitos clientes fora do Simples que precisam de crédito)
  - **Decisão crítica em set/2026**: empresas do Simples precisam optar entre regime unificado (tradicional) ou regime híbrido — o motor deve suportar simulação comparativa dos dois cenários
- **MEI**: cronograma próprio de valores fixos mensais (Anexo VII da LC 123/2006, incluído pela LC 214), com transição de 2027 a 2033
- **Split Payment**: mecanismo de recolhimento automático no momento do pagamento — relevante para o módulo de Efeito Caixa (Fase 3), mas o motor de cálculo da Fase 1 já deve registrar a informação de quando o split se aplica
- **Setor financeiro**: regime específico (spread bancário, intermediação) — fora do escopo do MVP, mas o motor não deve quebrar se encontrar CNAE desse setor (deve sinalizar "não suportado" em vez de calcular errado)
- **Não cumulatividade ampla**: crédito recuperável em toda a cadeia — relevante principalmente para o módulo de Crédito (Fase 2), mas o motor de cálculo da Fase 1 precisa registrar o crédito gerado por operação, mesmo que a tela de Crédito só venha depois

---

## 4. Estrutura de dados sugerida (motor parametrizável)

```
TabelaAliquotas {
  ano: int                    // 2026-2033+
  tributo: enum(CBS, IBS_estadual, IBS_municipal, IS, ICMS_residual, ISS_residual, PIS, COFINS)
  aliquota_base: decimal
  regra_neutralidade: boolean // true apenas em 2026
  fonte_normativa: string     // referência ao artigo/lei que fundamenta o valor
}

RegimeDiferenciado {
  ncm_ou_cnae: string
  percentual_reducao: decimal
  tributo_aplicavel: enum(CBS, IBS, ambos)
  ano_vigencia_inicio: int
  ano_vigencia_fim: int (nullable)
  fonte_normativa: string
}

RegimeEspecial {
  tipo: enum(SimplesNacional_Unificado, SimplesNacional_Hibrido, MEI, SetorFinanceiro, ...)
  regras_customizadas: json  // cada regime tem lógica própria, não generalizável
}
```

A tabela `fonte_normativa` em cada registro é obrigatória — permite auditoria de onde cada número veio, essencial para defender o cálculo perante um cliente ou em caso de mudança normativa.

---

## 5. Algoritmo de cálculo (visão geral, por NF-e processada)

1. Extrair do XML: NCM, CFOP, valor da operação, tributos atuais destacados
2. Identificar regime aplicável (regra geral, diferenciado, ou especial) via NCM/CNAE
3. Para cada ano do cronograma (2026–2033):
   a. Buscar alíquotas vigentes naquele ano em `TabelaAliquotas`
   b. Aplicar reduções de `RegimeDiferenciado`, se houver
   c. Calcular tributo devido no regime atual (ICMS/ISS/PIS/COFINS/IPI vigentes naquele ano, considerando extinção gradual)
   d. Calcular tributo devido na reforma (IBS/CBS/IS vigentes naquele ano)
   e. Registrar ambos para comparação
4. Agregar por período (mês/ano) e por produto para a tela de "Impacto"

---

## 6. Casos de teste obrigatórios antes de liberar o motor

- [ ] Produto sem regime diferenciado, todos os anos 2026–2033 batem com cálculo manual de referência
- [ ] Produto de cesta básica (alíquota zero) calculado corretamente em todos os anos
- [ ] Empresa Simples Nacional — comparação regime unificado x híbrido
- [ ] Empresa MEI — cronograma de valor fixo 2027–2033
- [ ] Produto sujeito a Imposto Seletivo (ex.: bebida açucarada)
- [ ] NF-e com CNAE de setor financeiro — sistema sinaliza "não suportado", não calcula errado
- [ ] Ano de transição intermediário (ex.: 2030) com substituição parcial de ICMS/ISS

---

## 7. Fontes consultadas (para validação, não para cópia)

**Fontes primárias:**
- Texto compilado da LC 214/2025 — planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm (contém também as alterações feitas pela LC 227/2026)
- Receita Federal — página oficial "Entenda a Reforma Tributária do Consumo" (gov.br/receitafederal), que confirma o cronograma 2029–2032 (90/80/70/60% ICMS+ISS, 10/20/30/40% IBS)

**Fontes secundárias (para contexto e exemplos práticos):**
- Pasqualino Contabilidade — alíquotas de transição 2026–2028
- Barbieri Advogados — guia completo LC 214/2025
- Fiscoplan — alíquotas-teste IBS/CBS
- Razonet / Algoritimado / Sisplan / Retenção na Fonte / Vinco — cronograma 2029–2032 e exemplos de cálculo (art. 128 do ADCT), todos convergentes com a fonte da Receita Federal
- Gilli Advogados — regra de redução de benefícios fiscais de ICMS
- e-Auditoria — LC 214 e Simples Nacional

**O que ainda precisa de validação com tributarista:**
- Alíquotas nominais exatas de referência do IBS/CBS (os ~8,8% + ~17,7% = ~26,5% citados são estimativas de mercado, não valores fixados em lei — dependem de resolução do Senado)
- Percentuais de redução por regime diferenciado (cesta básica, saúde, educação) NCM a NCM
- Regras do Simples Nacional híbrido x unificado em detalhe (decisão do contribuinte prevista para set/2026)
- Regime específico do setor financeiro e de combustíveis

---

*Próximo passo recomendado: sessão de validação com tributarista, artigo por artigo do cronograma, antes de qualquer linha de código do motor.*
