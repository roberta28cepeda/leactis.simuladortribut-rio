/**
 * TRACKER UNIVERSAL — Leactis
 * -----------------------------------------------------------------
 * Registra acessos, cliques e formulários de qualquer site Leactis
 * na tabela central `site_events` do Supabase.
 *
 * Instalação: <script src="/js/tracker.js"></script> no fim do <body>.
 * O site é identificado pelo endereço (MAPA_SITES). Para um site novo,
 * declare antes: <script>window.SITE_ORIGEM = "nome-do-site";</script>
 *
 * Para sites com navegação própria (SPA) ou formulário próprio:
 *   window.leactisTrack("pageview");
 *   window.leactisTrack("form_submit", { elemento: "contato" });
 * -----------------------------------------------------------------
 */
(function () {
  "use strict";

  var SUPABASE_URL = "https://lqzrdjwyueyeapaabhwu.supabase.co";
  var SUPABASE_ANON_KEY = "sb_publishable_lI9dWdkFgAc1xB6IP6I60A_GvweJOW9";
  var ENDPOINT = SUPABASE_URL + "/rest/v1/site_events";

  var MAPA_SITES = {
    "leactis.com.br": "leactis-principal",
    "www.leactis.com.br": "leactis-principal",
    "simulador.leactis.com.br": "leactis-simulador",
    "blog.leactis.com.br": "leactis-blog",
    "fantastic-gumdrop-c2678d.netlify.app": "leactis-analise-tributaria",
    "timely-malabi-29c1fe.netlify.app": "leactis-diagnostico-rapido",
    "delicate-zabaione-64a1b9.netlify.app": "leactis-triagem-a",
    "fanciful-shortbread-72ca7a.netlify.app": "leactis-triagem-b",
    "leactis-site-dglc.vercel.app": "leactis-principal",
    "leactis-site.vercel.app": "leactis-site-antigo",
    "leactis-site-4e4c.vercel.app": "leactis-site-antigo",
    "leactis-site-kaxv.vercel.app": "leactis-site-antigo",
    "leactis-site-h5w7.vercel.app": "leactis-site-antigo",
    "capta-fiscal-monitor.vercel.app": "capta-fiscal"
  };

  var host = window.location.hostname;
  var SITE_ORIGEM = window.SITE_ORIGEM || MAPA_SITES[host] || host;

  function getSessionId() {
    try {
      var sid = sessionStorage.getItem("_lx_sid");
      if (!sid) {
        sid = "sid_" + Date.now() + "_" + Math.random().toString(36).slice(2, 10);
        sessionStorage.setItem("_lx_sid", sid);
      }
      return sid;
    } catch (e) {
      return "sid_sem_storage";
    }
  }

  function getUtms() {
    try {
      var stored = sessionStorage.getItem("_lx_utm");
      if (stored) return JSON.parse(stored);
      var params = new URLSearchParams(window.location.search);
      var utms = {
        utm_source: params.get("utm_source") || null,
        utm_medium: params.get("utm_medium") || null,
        utm_campaign: params.get("utm_campaign") || null
      };
      sessionStorage.setItem("_lx_utm", JSON.stringify(utms));
      return utms;
    } catch (e) {
      return { utm_source: null, utm_medium: null, utm_campaign: null };
    }
  }

  function paginaAtual() {
    return window.location.pathname + (window.location.hash || "");
  }

  var ultimoPageview = { pagina: null, t: 0 };

  function enviarEvento(tipoEvento, extras) {
    extras = extras || {};
    var pagina = paginaAtual();

    // Evita contar duas vezes a mesma página em sequência (carga + roteador do site)
    if (tipoEvento === "pageview") {
      var agora = Date.now();
      if (ultimoPageview.pagina === pagina && agora - ultimoPageview.t < 1500) return;
      ultimoPageview = { pagina: pagina, t: agora };
    }

    var utms = getUtms();
    var payload = {
      site_origem: SITE_ORIGEM,
      tipo_evento: tipoEvento,
      pagina: pagina,
      session_id: getSessionId(),
      referrer: document.referrer || null,
      user_agent: navigator.userAgent,
      utm_source: utms.utm_source,
      utm_medium: utms.utm_medium,
      utm_campaign: utms.utm_campaign
    };
    for (var key in extras) {
      if (Object.prototype.hasOwnProperty.call(extras, key)) payload[key] = extras[key];
    }

    try {
      fetch(ENDPOINT, {
        method: "POST",
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: "Bearer " + SUPABASE_ANON_KEY,
          "Content-Type": "application/json",
          Prefer: "return=minimal"
        },
        body: JSON.stringify(payload),
        keepalive: true
      }).catch(function () {});
    } catch (e) {
      // Nunca deve quebrar o site
    }
  }

  window.leactisTrack = enviarEvento;

  // 1) Pageview ao carregar
  enviarEvento("pageview");

  // 2) Cliques: elementos com data-track, botões .btn, WhatsApp, telefone e e-mail
  document.addEventListener(
    "click",
    function (ev) {
      var el = ev.target.closest(
        "[data-track], .btn, a[href*='wa.me'], a[href^='tel:'], a[href^='mailto:']"
      );
      if (!el) return;
      var label =
        el.getAttribute("data-track") ||
        (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60) ||
        el.getAttribute("href") ||
        "clique-sem-nome";
      var href = el.getAttribute("href");
      if (href && /wa\.me|^tel:|^mailto:/.test(href)) label = label + " [" + href.split("?")[0] + "]";
      enviarEvento("click", { elemento: label });
    },
    true
  );

  // 3) Formulários HTML comuns (sites com <form>). Campos de senha, ocultos,
  //    arquivos e honeypot não são enviados.
  document.addEventListener(
    "submit",
    function (ev) {
      var form = ev.target;
      if (!(form instanceof HTMLFormElement)) return;
      var dados = {};
      Array.prototype.forEach.call(form.elements, function (field) {
        if (!field.name) return;
        var tipo = (field.type || "").toLowerCase();
        if (tipo === "password" || tipo === "hidden" || tipo === "file" || tipo === "submit") return;
        if (/^(hp|honeypot|_gotcha)/i.test(field.name)) return;
        if ((tipo === "checkbox" || tipo === "radio") && !field.checked) return;
        dados[field.name] = field.value;
      });
      enviarEvento("form_submit", {
        elemento: form.getAttribute("id") || form.getAttribute("name") || "formulario",
        dados: dados
      });
    },
    true
  );
})();
