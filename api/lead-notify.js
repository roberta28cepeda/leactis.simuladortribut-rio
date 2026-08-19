// Função serverless (Vercel) que recebe o Database Webhook do Supabase
// disparado a cada novo lead em `leactis_leads` e envia um e-mail de aviso
// via Resend. As credenciais (RESEND_API_KEY, RESEND_TO_EMAIL,
// LEAD_WEBHOOK_SECRET) moram só em variáveis de ambiente da Vercel --
// nunca no código que roda no navegador. Veja README.md.

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'method not allowed' });
    return;
  }

  const expectedSecret = process.env.LEAD_WEBHOOK_SECRET;
  const receivedSecret = req.headers['x-webhook-secret'];
  if (!expectedSecret || receivedSecret !== expectedSecret) {
    res.status(401).json({ error: 'unauthorized' });
    return;
  }

  const record = req.body && req.body.record;
  if (!record || !record.nome) {
    res.status(400).json({ error: 'payload inválido' });
    return;
  }

  const apiKey = process.env.RESEND_API_KEY;
  const toEmail = process.env.RESEND_TO_EMAIL;
  if (!apiKey || !toEmail) {
    // Não configurado ainda: responde 200 pra não deixar o webhook do
    // Supabase marcado como falha, mas não envia nada.
    res.status(200).json({ skipped: true, reason: 'Resend não configurado' });
    return;
  }

  const criadoEm = record.created_at
    ? new Date(record.created_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })
    : '';

  const html = `
    <h2>Novo lead no Simulador da Reforma Tributária</h2>
    <p><strong>Nome:</strong> ${escapeHtml(record.nome)}</p>
    <p><strong>WhatsApp:</strong> ${escapeHtml(record.whatsapp || '(não informado)')}</p>
    <p><strong>E-mail:</strong> ${escapeHtml(record.email || '(não informado)')}</p>
    <p><strong>Resumo da simulação:</strong><br>${escapeHtml(record.desafio || '')}</p>
    <p style="color:#888;font-size:12px">Recebido em ${criadoEm}</p>
  `;

  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'authorization': 'Bearer ' + apiKey,
      },
      body: JSON.stringify({
        from: process.env.RESEND_FROM || 'Simulador Leactis <onboarding@resend.dev>',
        to: [toEmail],
        subject: 'Novo lead: ' + record.nome + ' (Simulador Reforma Tributária)',
        html,
      }),
    });
    if (!r.ok) {
      const errBody = await r.text().catch(() => '');
      console.error('Resend falhou', r.status, errBody);
      res.status(502).json({ error: 'falha ao enviar e-mail' });
      return;
    }
    res.status(200).json({ sent: true });
  } catch (e) {
    console.error('lead-notify erro', e);
    res.status(502).json({ error: 'falha ao enviar e-mail' });
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
