# Roteiro de validação — Ferramenta de Análise de Impacto da Reforma Tributária

**Objetivo:** descobrir, com 5–10 escritórios de contabilidade, qual dor relacionada à Reforma Tributária é mais urgente hoje — relatório para cliente, cálculo de crédito, precificação, ou outra que ainda não apareceu no PRD — para definir o MVP mínimo viável antes de codar o motor de cálculo.

**Regra de ouro da entrevista:** você não está vendendo nada ainda. Está pesquisando. Pergunte sobre o que a pessoa **já fez** (comportamento passado), não sobre o que ela **acha que faria** (opinião sobre hipótese). "Você usaria uma ferramenta assim?" quase sempre gera um "sim, com certeza!" educado que não significa nada — evite esse tipo de pergunta até o fim, e mesmo assim com cautela.

---

## Antes de ligar

- **Quem entrevistar:** priorize sócios ou responsáveis técnicos de escritórios que já atendem empresas fora do Simples (Lucro Real/Presumido), porque são os mais expostos à complexidade do IBS/CBS. Escritórios pequenos/médios tendem a ter mais dor (menos recurso pra bancar retrabalho) do que os grandes (que já têm equipe tributária dedicada).
- **Como abordar:** não peça "uma entrevista sobre meu produto". Peça 20–30 minutos pra entender como escritórios estão lidando com a Reforma Tributária — as pessoas adoram falar sobre um problema que estão vivendo.
- **Grave (com permissão) ou tenha alguém anotando.** Você vai ouvir 5–10 dessas, misturar os detalhes é fácil.

---

## Roteiro (30–40 min)

### 1. Abertura e contexto (5 min)
- Quantos clientes o escritório atende hoje, e quantos estão fora do Simples Nacional (Lucro Real/Presumido)?
- Qual o tamanho da equipe, e quem hoje toca os temas tributários mais complexos?

### 2. Situação atual — como fazem hoje (10 min)
*(O objetivo aqui é entender o processo real, não o processo ideal.)*
- Me conta como foi a última vez que vocês precisaram explicar pra um cliente o impacto da Reforma Tributária no negócio dele. O que vocês fizeram, passo a passo?
- Quanto tempo levou, do início ao fim, essa análise?
- Que ferramentas vocês usaram — planilha própria, algum sistema, cálculo manual?
- Quem no escritório fez esse trabalho? Foi fácil delegar, ou só uma pessoa específica consegue fazer?
- **Se não tiverem feito isso ainda:** por que não? Falta de tempo, falta de clareza nas regras, cliente não perguntou, ou vocês não se sentem seguros pra fazer essa análise ainda?

### 3. Cavando a dor específica (10 min)
*(Aqui é onde normalmente aparece a dor real — deixe a pessoa falar, não complete as frases dela.)*
- Qual foi a parte mais chata ou mais demorada desse processo?
- Já aconteceu de vocês perceberem um erro depois de já ter passado a análise pro cliente? O que aconteceu?
- Se pudesse tirar uma única tarefa braçal da sua rotina relacionada a isso, qual seria?
- Como está o clima com os clientes em relação a esse assunto — eles estão perguntando, cobrando, ansiosos? Me dá um exemplo de uma conversa recente.

### 4. Testando as 3 hipóteses do PRD (5–8 min)
*(Não liste as três de uma vez — deixe a pessoa mencionar espontaneamente antes de você citar as outras. Isso evita viés de "a última opção que ele disse parece a melhor".)*
- Das seguintes frentes, qual pesa mais no dia a dia de vocês hoje: **(a)** montar um relatório/projeção pra apresentar ao cliente, **(b)** calcular o crédito tributário que a empresa vai acumular/usar, ou **(c)** simular o efeito na precificação/margem dos produtos?
- Por quê essa e não as outras? (busque o motivo — urgência do cliente, complexidade técnica, volume de trabalho)
- Tem alguma outra dor relacionada à Reforma que não é nenhuma dessas três e que vocês sentem mais?

### 5. Validando a operação/dados (5 min)
*(Isso valida se a arquitetura técnica do MVP — upload de XML de NF-e — faz sentido operacionalmente.)*
- Vocês têm acesso fácil aos XMLs de NF-e dos seus clientes? De onde tiram — sistema próprio do cliente, contabilidade já integrada, ou é um processo manual de pedir pro cliente exportar?
- Em média, quantas notas por mês um cliente típico de vocês emite?
- Os clientes de vocês usam sistemas de emissão muito diferentes entre si, ou tem um padrão?

### 6. Reação ao conceito (só agora, com cautela) (5 min)
*(Agora sim você pode descrever a ideia — mas ainda observando reação, não pedindo validação.)*
- Descreva rapidamente: "Imagina uma ferramenta onde você sobe os XMLs de NF-e de um cliente e em minutos recebe uma comparação clara de quanto ele paga hoje x quanto vai pagar com a reforma, ano a ano até 2033, pronta pra apresentar."
- O que passou pela sua cabeça agora? (deixe reagir livremente antes de qualquer pergunta fechada)
- Isso resolveria a dor que você descreveu antes, ou é uma coisa diferente?
- **Pergunta de compromisso (a que realmente importa):** se essa ferramenta existisse hoje, gratuita, em versão piloto, topariam testar com um cliente real nas próximas semanas e me dar feedback sincero? *(Um "sim" aqui com disposição de agendar já vale mais que 10 "usaria sim" genéricos.)*

### 7. Fechamento (2 min)
- Teria mais 1 ou 2 escritórios parecidos com o de vocês que valeria eu conversar?
- Posso voltar a falar com você depois que eu tiver algo pra mostrar?

---

## Sinais de alerta durante a conversa

- Respostas genéricas e educadas demais ("é interessante", "seria útil") sem exemplo concreto — sinal de dor fraca ou inexistente.
- Ninguém consegue contar uma história específica e recente de quando isso deu problema — sinal de que a dor não é tão urgente quanto o PRD supõe.
- Todo mundo responde "relatório pro cliente" só porque foi a primeira opção que você citou — cuidado com o viés de ordem, é por isso que a pergunta 4 pede pra deixar a pessoa falar antes.
- Ninguém topa o teste piloto no item 6 — é o sinal mais forte de todos. Interesse sem compromisso de tempo real geralmente não vira uso de verdade.

---

## Ficha de registro (preencher logo depois de cada conversa, enquanto está fresco)

```
Escritório: ___________________  Data: __________
Nº de clientes fora do Simples: _______
Dor principal citada (nas palavras da pessoa, não resumida): 
_________________________________________________

Qual das 3 frentes pesou mais (a/b/c/outra): _______
Motivo dado: _________________________________________________

Têm acesso fácil a XML de NF-e? (sim/não/depende): _______
Volume médio de notas/mês por cliente: _______

Topou ser piloto? (sim/não/talvez): _______
Frase mais forte que a pessoa disse (cite literalmente):
_________________________________________________

Nota geral de urgência da dor (1-5, sendo 5 = "precisa disso ontem"): ___
```

## Depois das 5–10 entrevistas

Junte todas as fichas e responda:
1. Qual das 3 frentes (ou uma quarta que apareceu) teve mais menções como dor principal?
2. Quantos toparam ser piloto de verdade?
3. O padrão de acesso a XML de NF-e é consistente o suficiente pra validar a arquitetura técnica do MVP, ou apareceu um obstáculo recorrente (ex: "meus clientes não me mandam XML, só PDF")?
4. Alguma dor apareceu que não está no PRD? Vale reabrir o documento e ajustar o MVP antes de qualquer linha de código.

Essa consolidação é o que decide o escopo real do MVP — não o PRD como está hoje.
