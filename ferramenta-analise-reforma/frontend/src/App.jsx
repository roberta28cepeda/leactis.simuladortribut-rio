import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const fmt = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

function TelaUpload({ onAnalisado }) {
  const [nomeCliente, setNomeCliente] = useState("");
  const [cnpjCliente, setCnpjCliente] = useState("");
  const [arquivos, setArquivos] = useState([]);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar() {
    if (!nomeCliente || arquivos.length === 0) {
      setErro("Informe o nome do cliente e selecione ao menos um arquivo XML ou .zip.");
      return;
    }
    setErro(null);
    setEnviando(true);
    try {
      const form = new FormData();
      form.append("nome_cliente", nomeCliente);
      if (cnpjCliente) form.append("cnpj_cliente", cnpjCliente);
      for (const arquivo of arquivos) form.append("arquivos", arquivo);

      const r = await fetch(`${API_URL}/api/analises`, { method: "POST", body: form });
      if (!r.ok) throw new Error("Falha ao processar os arquivos.");
      const resumo = await r.json();

      const r2 = await fetch(`${API_URL}/api/analises/${resumo.id}`);
      if (!r2.ok) throw new Error("Falha ao carregar o resultado.");
      onAnalisado(await r2.json());
    } catch (e) {
      setErro(e.message || "Erro inesperado ao enviar.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: "40px auto", padding: "0 20px" }}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Análise de Impacto da Reforma Tributária</h1>
      <p style={{ color: "#556", marginBottom: 24 }}>
        Envie os XMLs de NF-e do cliente (ou um .zip com vários) para comparar a carga
        tributária atual x reforma, ano a ano.
      </p>

      <div style={{ background: "#F5F5F8", border: "1px solid #E0E0E5", borderRadius: 8, padding: 24 }}>
        <label style={{ display: "block", marginBottom: 14 }}>
          <span style={{ display: "block", fontSize: 13, marginBottom: 4 }}>Nome do cliente</span>
          <input
            value={nomeCliente} onChange={(e) => setNomeCliente(e.target.value)}
            style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "block", marginBottom: 14 }}>
          <span style={{ display: "block", fontSize: 13, marginBottom: 4 }}>CNPJ (opcional)</span>
          <input
            value={cnpjCliente} onChange={(e) => setCnpjCliente(e.target.value)}
            style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "block", marginBottom: 18 }}>
          <span style={{ display: "block", fontSize: 13, marginBottom: 4 }}>XMLs de NF-e (ou .zip)</span>
          <input
            type="file" multiple accept=".xml,.zip"
            onChange={(e) => setArquivos(Array.from(e.target.files))}
          />
        </label>

        {erro && <p style={{ color: "#b3271f", fontSize: 13, marginBottom: 12 }}>{erro}</p>}

        <button
          onClick={enviar} disabled={enviando}
          style={{
            background: "#0B2341", color: "#fff", border: "none", borderRadius: 4,
            padding: "10px 20px", fontWeight: 600, cursor: enviando ? "not-allowed" : "pointer",
          }}
        >
          {enviando ? "Processando..." : "Gerar análise"}
        </button>
      </div>
    </div>
  );
}

function TelaResultado({ analise, onNovaAnalise }) {
  const barData = analise.impacto_por_ano.map((i) => ({
    ano: i.ano,
    "Regime atual": Math.round(i.carga_atual),
    "Com a reforma": Math.round(i.carga_reforma),
  }));

  return (
    <div style={{ maxWidth: 860, margin: "40px auto", padding: "0 20px" }}>
      <button onClick={onNovaAnalise} style={{ background: "none", border: "none", color: "#0B6", cursor: "pointer", marginBottom: 16, padding: 0 }}>
        ← Nova análise
      </button>
      <h1 style={{ fontSize: 22, marginBottom: 2 }}>{analise.nome_cliente}</h1>
      {analise.cnpj_cliente && <p style={{ color: "#667", marginBottom: 4 }}>{analise.cnpj_cliente}</p>}
      <p style={{ color: "#667", marginBottom: 20 }}>
        {analise.total_notas_processadas} de {analise.total_notas_recebidas} notas processadas
        {analise.total_notas_com_erro > 0 && ` — ${analise.total_notas_com_erro} com erro de leitura`}
      </p>

      {analise.aviso_parametros_nao_validados && (
        <div style={{ background: "#FFF4E5", border: "1px solid #F0C674", borderRadius: 6, padding: 14, marginBottom: 20, fontSize: 13.5 }}>
          ⚠️ {analise.aviso_parametros_nao_validados}
        </div>
      )}

      <div style={{ height: 320, marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="ano" />
            <YAxis tickFormatter={(v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : `${Math.round(v)}`)} />
            <Tooltip formatter={(v) => fmt(v)} />
            <Legend />
            <Bar dataKey="Regime atual" fill="#0B2341" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Com a reforma" fill="#2AD8C4" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 24, fontSize: 14 }}>
        <thead>
          <tr style={{ background: "#F5F5F8", textAlign: "right" }}>
            <th style={{ textAlign: "left", padding: 8 }}>Ano</th>
            <th style={{ padding: 8 }}>Regime atual</th>
            <th style={{ padding: 8 }}>Com a reforma</th>
            <th style={{ padding: 8 }}>Diferença</th>
          </tr>
        </thead>
        <tbody>
          {analise.impacto_por_ano.map((i) => (
            <tr key={i.ano} style={{ borderBottom: "1px solid #eee", textAlign: "right" }}>
              <td style={{ textAlign: "left", padding: 8 }}>{i.ano}</td>
              <td style={{ padding: 8 }}>{fmt(i.carga_atual)}</td>
              <td style={{ padding: 8 }}>{fmt(i.carga_reforma)}</td>
              <td style={{ padding: 8, color: i.diferenca >= 0 ? "#b3271f" : "#0a7d4f" }}>
                {i.diferenca >= 0 ? "+" : ""}{fmt(i.diferenca)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {analise.erros.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontWeight: 600, marginBottom: 6 }}>Arquivos com erro de leitura:</p>
          <ul style={{ fontSize: 13, color: "#b3271f" }}>
            {analise.erros.map((e, idx) => (
              <li key={idx}>{e.nome_arquivo}: {e.motivo}</li>
            ))}
          </ul>
        </div>
      )}

      <a
        href={`${API_URL}/api/analises/${analise.id}/pdf`}
        style={{
          display: "inline-block", background: "#0B2341", color: "#fff",
          padding: "10px 20px", borderRadius: 4, textDecoration: "none", fontWeight: 600,
        }}
      >
        Exportar PDF
      </a>

      <p style={{ fontSize: 12, color: "#889", marginTop: 24 }}>
        Análise simulada, gerada automaticamente. Não substitui parecer técnico assinado
        por contador ou tributarista responsável.
      </p>
    </div>
  );
}

export default function App() {
  const [analise, setAnalise] = useState(null);

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", minHeight: "100vh", background: "#fff", color: "#1a1a1a" }}>
      {analise
        ? <TelaResultado analise={analise} onNovaAnalise={() => setAnalise(null)} />
        : <TelaUpload onAnalisado={setAnalise} />}
    </div>
  );
}
