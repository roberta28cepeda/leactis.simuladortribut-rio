# Simulador da Reforma Tributária — Leactis

Landing page estática (HTML/CSS/JS puro, sem framework nem build) para
campanhas de anúncio pago (Google Ads / Meta Ads). Simula, ano a ano de 2027
a 2033, quanto uma empresa pagaria em 3 caminhos possíveis durante a
transição da Reforma Tributária — Guia única (Simples Nacional), regime
híbrido (Simples + CBS/IBS por fora) e Lucro Presumido — e só libera o
resultado depois que a pessoa deixa nome e WhatsApp.

Projeto separado do site institucional da Leactis (`leactis-site`): não
compartilha repositório, deploy nem domínio. As referências visuais (cores,
fontes, logo) foram copiadas para cá para manter a identidade da marca, mas
qualquer alteração de marca no site principal não se reflete aqui
automaticamente.

## Estrutura

```
index.html         a página inteira (HTML + CSS específico + JS de cálculo/UI)
css/leactis.css     tokens de marca (cores, tipografia) e componentes reaproveitados
fonts/               Barlow e Barlow Condensed (usadas pela marca Leactis)
img/                 logo, ícones e imagem de Open Graph
favicon.ico, apple-touch-icon.png, site.webmanifest   ícones do navegador
vercel.json          headers de cache para deploy na Vercel
```

## Rodando localmente

Não precisa de Node nem de build:

```bash
python3 -m http.server 8000
# abra http://localhost:8000/
```

## Deploy na Vercel

1. Crie uma conta em [vercel.com](https://vercel.com) (dá pra logar com a conta do GitHub) e importe este repositório.
2. Não precisa mudar nenhuma configuração de build — é um site estático puro, a Vercel detecta sozinha.
3. Deploy. Você recebe uma URL do tipo `algo.vercel.app`.
4. **Domínio próprio (`simulador.leactis.com.br`):** no projeto, vá em **Settings → Domains**, digite `simulador.leactis.com.br` e clique em **Add**. A Vercel mostra um registro **CNAME** pra você cadastrar no provedor de DNS do domínio `leactis.com.br` (Registro.br, ou outro DNS se o domínio tiver sido apontado pra lá):
   - **Tipo:** CNAME
   - **Nome/Host:** `simulador`
   - **Valor/Destino:** `cname.vercel-dns.com.`

   Depois de cadastrar, a Vercel valida sozinha (pode levar de minutos a algumas horas pra propagar) e emite o certificado HTTPS automaticamente. As tags `canonical`, `og:image`, `og:url` e `twitter:image` do `index.html` já estão configuradas para `simulador.leactis.com.br` — só precisa trocar se decidir usar outro domínio/subdomínio.

## Captura de leads (Supabase)

O formulário (nome + WhatsApp, antes de liberar o resultado) grava direto
numa tabela do [Supabase](https://supabase.com) (plano grátis) via API REST
pública — sem função serverless própria.

**Importante:** use um projeto Supabase novo e separado, exclusivo deste
simulador — não reaproveite o mesmo projeto/tabela de outro site ou do CRM.

1. Crie uma conta grátis em [supabase.com](https://supabase.com) e um projeto novo (ex: "leactis-simulador").
2. No painel do projeto, abra **SQL Editor** e rode:
   ```sql
   create table public.leactis_leads (
     id uuid primary key default gen_random_uuid(),
     created_at timestamptz not null default now(),
     nome text not null,
     email text not null,
     whatsapp text,
     desafio text
   );

   alter table public.leactis_leads enable row level security;

   create policy "Permitir inserção pública de leads"
     on public.leactis_leads
     for insert
     to anon
     with check (true);
   ```
   Isso cria a tabela e libera **só a inserção** pra chave pública (`anon`) —
   ninguém de fora consegue ler, alterar ou apagar os leads com essa chave,
   só você, entrando no painel do Supabase com sua conta.
3. Vá em **Settings → API** e copie dois valores: **Project URL** e a chave
   **anon public** (não a `service_role`, essa nunca deve ir pro código do
   site).
4. Abra `index.html`, ache (perto do fim do `<script>`, antes do listener do
   botão "Ver meu resultado agora"):
   ```js
   var SUPABASE_URL = 'https://SEU_PROJETO.supabase.co';
   var SUPABASE_ANON_KEY = 'SUA_ANON_KEY';
   ```
   e troque pelos valores copiados.
5. Commit + push — a Vercel reimplanta sozinha a cada push na branch principal.

Enquanto isso não for feito, o botão mostra "Formulário ainda não
configurado" em vez de fingir que enviou o lead — ele nunca finge sucesso.

Pra ver os leads recebidos: painel do Supabase → **Table Editor** →
`leactis_leads`. Cada lead vem com o prefixo `[Simulador Reforma
Tributária]` no campo `desafio`, junto com o resumo da simulação (faturamento,
atividade, ano e opção mais econômica).

## Aviso por e-mail a cada lead novo (opcional, mas recomendado)

Sem isso, os leads só ficam armazenados no Supabase — ninguém é avisado, e é
fácil esquecer de checar a tabela e deixar o lead esfriar. `api/lead-notify.js`
é uma função serverless (Vercel) que recebe um aviso do Supabase a cada
`INSERT` em `leactis_leads` e manda um e-mail via [Resend](https://resend.com)
(plano grátis: 100 e-mails/dia, 3.000/mês).

1. Crie uma conta grátis em [resend.com](https://resend.com), de preferência
   **com o e-mail onde você quer receber os avisos** (ex: `contato@leactis.com.br`)
   — sem verificar um domínio próprio no Resend, ele só entrega e-mails de
   teste para o endereço da própria conta, o que já resolve pra esse uso.
2. Em **API Keys**, crie uma chave nova e copie o valor (só aparece uma vez).
3. No painel da Vercel, no projeto, vá em **Settings → Environment Variables**
   e adicione três variáveis:
   - `RESEND_API_KEY` = a chave do passo 2
   - `RESEND_TO_EMAIL` = o e-mail que deve receber os avisos
   - `LEAD_WEBHOOK_SECRET` = uma senha aleatória só sua, pra garantir que
     só o Supabase consegue chamar essa função (qualquer string longa serve)
   Depois de salvar, force um redeploy (**Deployments → ⋯ → Redeploy** no
   último deploy) pra elas passarem a valer.
4. No painel do Supabase, vá em **Database → Webhooks → Create a new hook**:
   - **Table:** `leactis_leads`
   - **Events:** `Insert`
   - **Type:** `HTTP Request`
   - **URL:** `https://SEU-DOMINIO-OU-PROJETO.vercel.app/api/lead-notify`
     (troque pela URL real do seu deploy, ou por `https://simulador.leactis.com.br/api/lead-notify`
     depois que o domínio próprio estiver ativo)
   - **HTTP Headers:** adicione `x-webhook-secret` com o mesmo valor de
     `LEAD_WEBHOOK_SECRET` do passo 3
   - Salve.
5. Teste: preencha o simulador de ponta a ponta com um lead de teste — o
   e-mail deve chegar em alguns segundos.

Enquanto `RESEND_API_KEY`/`RESEND_TO_EMAIL` não estiverem configuradas, a
função responde normalmente (200) sem enviar nada — ela nunca deixa o
Supabase com o webhook marcado como falha.

## Rastreamento de anúncios (GA4 e Meta Pixel)

A página já vem com os dois blocos prontos no `<head>`, desligados por
padrão — enquanto os IDs não forem trocados, nenhum script é carregado e
nenhuma requisição de rede é feita.

1. **Google Ads / GA4:** crie uma propriedade em [analytics.google.com](https://analytics.google.com), copie o Measurement ID (`G-XXXXXXXXXX`) e troque em:
   ```js
   window.LEACTIS_GA_ID = 'G-XXXXXXXXXX';
   ```
2. **Meta Pixel:** crie um pixel no [Gerenciador de Eventos do Meta Business](https://business.facebook.com/events_manager), copie o Pixel ID e troque em:
   ```js
   window.LEACTIS_META_PIXEL_ID = '0000000000000000';
   ```
3. Commit + push. A página já dispara o evento `generate_lead` (GA4) e `Lead`
   (Meta Pixel) automaticamente no momento em que alguém preenche nome e
   WhatsApp e libera o resultado — não precisa configurar nada a mais pro
   básico de conversão funcionar.

## Base legal e avisos

As alíquotas de referência de CBS (~8,8%) e IBS (~17,7%) usadas na simulação
são estimativas e ainda dependem de resolução do Senado Federal (art. 349,
LC 214/2025). Base legal: EC 132/2023 e LC 214/2025. A simulação é uma
ferramenta de apoio à decisão e não substitui uma análise tributária
individualizada — isso já está explícito no rodapé da própria página.
