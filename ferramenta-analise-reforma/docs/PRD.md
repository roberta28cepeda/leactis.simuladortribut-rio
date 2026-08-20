# PRD — Ferramenta de Análise de Impacto da Reforma Tributária (MVP)

**Status:** Rascunho v1
**Público-alvo do produto:** Escritórios de contabilidade (B2B)
**Escopo deste documento:** Fase 1 (MVP) de um sistema completo, faseado

---

## 1. Problem Statement

Escritórios de contabilidade precisam orientar seus clientes (empresas) sobre o impacto da Reforma Tributária (IBS/CBS, LC 214/2025 e LC 228/2025) na margem, no caixa e no crédito tributário até 2033, mas hoje dependem de planilhas manuais, cruzamentos demorados e estimativas de mercado — não de dados reais da operação do cliente. Isso gera insegurança nas conversas com os clientes, retrabalho e risco de erro em um tema fiscal de alta complexidade e mudança constante. Sem uma ferramenta que automatize esse cálculo, o contador perde tempo, credibilidade e a oportunidade de se posicionar como consultor estratégico durante a transição.

---

## 2. Goals

1. Permitir que o contador faça upload de XML de NF-e de um cliente e receba, em minutos, uma comparação clara do imposto devido no regime atual x reforma, ano a ano (2026–2033).
2. Reduzir de dias/horas para minutos o tempo de geração de uma análise de impacto tributário por cliente.
3. Entregar resultados baseados em dados reais da operação (não estimativas de mercado), aumentando a confiança do contador na conversa com o cliente.
4. Validar com 10–15 escritórios-piloto que o cálculo está correto e que a análise gerada é útil o suficiente para ser apresentada a um cliente final.
5. Estabelecer a base técnica (motor de regras parametrizável) que suportará as fases seguintes (crédito, precificação, efeito caixa, multi-cliente).

---

## 3. Non-Goals (fora do escopo do MVP)

- **Leitura de SPED (ECF/ECD/EFD)** — fica para Fase 2. O MVP usa apenas XML de NF-e, que é mais simples de parsear e já permite validar o motor de cálculo.
- **Módulo de crédito tributário (crédito x imposto devido)** — Fase 2.
- **Precificação e simulação de margem por produto** — Fase 3.
- **Efeito caixa e Split Payment** — Fase 3.
- **Gestão multi-cliente / dashboard de carteira para o contador** — Fase 2. No MVP, cada análise é feita para uma empresa por vez.
- **Integração com e-CAC** — Fase 4. Não é bloqueador para validar a proposta de valor central.
- **Precisão fiscal certificada/auditada** — o MVP é uma ferramenta de análise e simulação, não substitui parecer técnico assinado por contador responsável (isso deve estar explícito no produto).

---

## 4. User Stories

**Persona principal: Contador (usuário do escritório)**

- Como contador, quero fazer upload dos arquivos XML de NF-e de um cliente para que o sistema calcule automaticamente o impacto do IBS/CBS na operação dele.
- Como contador, quero ver a comparação entre o regime tributário atual e a reforma, ano a ano até 2033, para explicar ao cliente de forma visual e simples.
- Como contador, quero que o sistema identifique claramente quais produtos/NCMs têm alíquota reduzida ou diferenciada, para não errar na análise.
- Como contador, quero exportar essa análise em um formato apresentável (PDF/relatório) para enviar ao cliente.
- Como contador, quero ser avisado se algum XML enviado estiver corrompido, incompleto ou fora do padrão, para corrigir antes da análise sair errada.

**Persona secundária: Cliente final (empresário) — indireta no MVP**

- Como empresário, quero receber do meu contador uma projeção clara de quanto vou pagar de imposto nos próximos anos, para me planejar financeiramente.

---

## 5. Requirements

### Must-Have (P0)
- **Upload de XML de NF-e** (múltiplos arquivos ou lote em .zip)
- **Parser de XML** conforme schema da SEFAZ, extraindo: NCM, CFOP, valor da operação, tributos atuais destacados (ICMS, IPI, PIS, COFINS, ISS quando aplicável)
- **Motor de cálculo parametrizável** de IBS/CBS aplicando as alíquotas e regras de transição da LC 214/2025 e LC 228/2025, ano a ano (2026–2033)
  - Acceptance: dado um XML de venda de um produto sem redução de alíquota, o sistema calcula corretamente o IBS+CBS devido para cada ano do cronograma de transição
  - Acceptance: dado um produto com NCM sujeito a redução de alíquota (ex: cesta básica), o sistema aplica o percentual de redução correto
- **Tela de resultado "Impacto"**: gráfico comparando carga tributária atual x reforma, ano a ano
- **Tratamento de erro de upload**: XML inválido, corrompido ou de schema incompatível gera mensagem clara, não trava o sistema
- **Exportação do resultado em PDF**

### Nice-to-Have (P1)
- Upload direto via integração com sistema emissor de NF-e do cliente (em vez de exportar/importar manualmente)
- Filtro por período (analisar apenas um intervalo de datas das notas)
- Detalhamento por produto/NCM na tela de resultado (não só agregado)
- Múltiplos usuários por escritório (não só um login)

### Future Considerations (P2)
- Leitura de SPED (Fase 2)
- Módulo de crédito, precificação, efeito caixa (Fases 2–3)
- Multi-cliente / dashboard de carteira (Fase 2)
- Integração e-CAC (Fase 4)

---

## 6. Success Metrics

**Leading (semanas):**
- Taxa de conclusão do upload→resultado sem erro: meta 90%
- Tempo médio da análise (upload até resultado exibido): meta < 5 minutos para até 500 notas
- % de escritórios-piloto que geram pelo menos 2 análises na primeira semana: meta 60%

**Lagging (1–3 meses):**
- % de escritórios-piloto que validam o cálculo como "correto" com um tributarista de referência: meta 100% (é inegociável — erro aqui destrói a credibilidade do produto)
- % de escritórios que apresentam o relatório gerado a um cliente final: meta 40%
- Taxa de conversão piloto → assinante pago: meta a definir após validação

---

## 7. Open Questions

- **[Tributário — bloqueante]** Quais regras específicas da LC 214/2025 e LC 228/2025 já estão regulamentadas o suficiente para cálculo confiável em 2026, e quais dependem de normativas complementares ainda não publicadas?
- **[Tributário — bloqueante]** Como tratar setores com regras especiais (Simples Nacional híbrido, imunidades, regimes diferenciados)? O MVP vai suportar todos os regimes ou só Lucro Real/Presumido inicialmente?
- **[Produto — não bloqueante]** O relatório exportado deve ter selo/aviso de "análise simulada, não substitui parecer técnico"? (Recomendo que sim, por proteção legal.)
- **[Engenharia — não bloqueante]** O parser de XML vai validar contra o XSD oficial da SEFAZ ou fazer parsing tolerante a variações de emissor?
- **[Negócio — não bloqueante]** Modelo de precificação: por empresa analisada, por escritório (assinatura), ou por volume de notas processadas?

---

## 8. Timeline Considerations

- **Dependência crítica**: a regulamentação da Reforma Tributária está sendo publicada em fases pelo Comitê Gestor do IBS e pela Receita Federal. O motor de cálculo precisa ser parametrizável desde o início para absorver mudanças normativas sem reescrever código.
- **Fase 1 (MVP)**: parser NF-e + cálculo básico + tela de impacto — sugestão de 8–12 semanas com 1 dev + 1 tributarista validando
- **Fase 2**: SPED + crédito + multi-cliente
- **Fase 3**: precificação + efeito caixa
- **Fase 4**: e-CAC + polimento

---

*Documento gerado como ponto de partida. Requer validação de um tributarista antes de qualquer decisão de arquitetura do motor de cálculo.*
