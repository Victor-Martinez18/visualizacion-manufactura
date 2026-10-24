"""
Avance 4 – Dashboard final: Cumplimiento del programa de producción
Genera outputs/dashboard/index.html, un dashboard interactivo autocontenido (no requiere internet).

Estructura (teoría 4.2.4, jerarquía en 3 niveles):
  Nivel 1 · Vista general   → mensaje principal + KPIs
  Nivel 2 · Tendencia y comparación → retrasos por día (insight) y máquinas con IC 95 %
  Nivel 3 · Detalle diagnóstico     → tabla por máquina
Interactividad: filtro por tipo de operación (recalcula todo) y tooltips en las gráficas.

Uso (desde la raíz del proyecto):  python src/dashboard_final.py
Entrada: data/processed/hybrid_manufacturing_clean.csv (generado por el notebook)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from plotly.offline import get_plotlyjs
from scipy.stats import chi2_contingency

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "processed" / "hybrid_manufacturing_clean.csv"
OUT = ROOT / "outputs" / "dashboard" / "index.html"
OUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CLEAN, parse_dates=["Fecha", "Scheduled_Start"])
DIAS = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
MAQ = sorted(df["Machine_ID"].unique())


def wilson(k, n, z=1.96):
    """Intervalo de confianza de Wilson al 95 % para una proporción."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return p, c - h, c + h


def resumen(sub):
    """Calcula todo lo que muestra el dashboard para un subconjunto de órdenes."""
    n = len(sub)
    ret = sub["Estado"] == "Retrasada"
    fal = sub["Estado"] == "Fallida"
    h_tot = sub["Processing_Time"].sum() / 60
    h_fal = sub.loc[fal, "Processing_Time"].sum() / 60

    # Nivel 2a · por día (días completos vs parciales)
    dias = []
    for f, g in sub.groupby("Fecha"):
        dias.append({"fecha": f.strftime("%Y-%m-%d"),
                     "etq": f"{DIAS[f.weekday()]} {f.day}",
                     "n": int(len(g)),
                     "ret": float((g["Estado"] == "Retrasada").mean()),
                     "fal": float((g["Estado"] == "Fallida").mean()),
                     "parcial": bool(f.day in (18, 25))})
    completos = sub[sub["Fecha"].dt.day.between(19, 24)]
    mid = completos["Fecha"].dt.day.between(21, 23)
    ret_mid = float((completos.loc[mid, "Estado"] == "Retrasada").mean())
    ret_resto = float((completos.loc[~mid, "Estado"] == "Retrasada").mean())

    # Nivel 2b · por máquina con IC 95 % y prueba ji cuadrada
    maq = []
    for m in MAQ:
        g = sub[sub["Machine_ID"] == m]
        p, lo, hi = wilson(int(g["Incumplimiento"].sum()), len(g))
        maq.append({"m": m, "n": int(len(g)), "p": p, "lo": lo, "hi": hi})
    pval = float(chi2_contingency(pd.crosstab(sub["Machine_ID"], sub["Estado"]))[1])

    # Nivel 3 · tabla por máquina
    tabla = []
    for m in MAQ:
        g = sub[sub["Machine_ID"] == m]
        tabla.append({"m": m, "n": int(len(g)),
                      "comp": float((g["Estado"] == "Completada").mean()),
                      "ret": float((g["Estado"] == "Retrasada").mean()),
                      "fal": float((g["Estado"] == "Fallida").mean()),
                      "hfal": float(g.loc[g["Estado"] == "Fallida", "Processing_Time"].sum() / 60)})

    return {"n": int(n), "inc": float(sub["Incumplimiento"].mean()),
            "ret": float(ret.mean()), "fal": float(fal.mean()),
            "h_fal": float(h_fal), "h_tot": float(h_tot),
            "retraso_ret": float(sub.loc[ret, "Retraso_inicio_min"].mean()),
            "dias": dias, "ret_mid": ret_mid, "ret_resto": ret_resto,
            "maq": maq, "pval": pval, "tabla": tabla}


DATA = {"Todas las operaciones": resumen(df)}
for op in sorted(df["Operacion"].unique()):
    DATA[op] = resumen(df[df["Operacion"] == op])

HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cumplimiento del programa de producción</title>
<script>__PLOTLY__</script>
<style>
  :root { --ink:#1F2937; --muted:#6B7280; --line:#E5E7EB; --bg:#F7F7F5; --card:#FFFFFF;
          --ret:#E09A2B; --fal:#B8322A; --comp:#3A6EA5; --neutral:#9AA3AD; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font-family:"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif; }
  .wrap { max-width:1240px; margin:0 auto; padding:20px 24px 28px; }
  header { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; }
  .eyebrow { font-size:13px; color:var(--muted); letter-spacing:.02em; margin:0 0 2px; }
  h1 { font-size:20px; margin:0; font-weight:600; }
  .filtro label { font-size:12px; color:var(--muted); display:block; margin-bottom:4px; }
  .filtro select { font:inherit; font-size:14px; padding:6px 10px; border:1px solid #CBD5E1;
                   border-radius:6px; background:#fff; min-width:220px; }
  /* Nivel 1 */
  .hero { display:grid; grid-template-columns: 1.35fr 2fr; gap:20px; margin-top:16px;
          background:var(--card); border:1px solid var(--line); border-radius:10px; padding:20px 24px; }
  .hero .big { font-size:64px; font-weight:700; line-height:1; color:var(--fal); }
  .hero .msg { font-size:22px; font-weight:600; margin-top:8px; line-height:1.25; }
  .hero .sub { font-size:14px; color:var(--muted); margin-top:8px; line-height:1.45; }
  .kpis { display:grid; grid-template-columns:repeat(2, 1fr); gap:10px 18px; align-content:center; }
  .kpi { border-left:3px solid var(--line); padding:4px 0 4px 12px; }
  .kpi .v { font-size:26px; font-weight:600; }
  .kpi .l { font-size:13px; color:var(--muted); }
  .kpi.acc { border-left-color:var(--fal); }
  .kpi.ret { border-left-color:var(--ret); }
  /* Nivel 2 */
  .row2 { display:grid; grid-template-columns: 1.25fr 1fr; gap:20px; margin-top:20px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px 8px; }
  .card h2 { font-size:16px; margin:0; font-weight:600; }
  .card p.note { font-size:13px; color:var(--muted); margin:4px 0 0; }
  .chart { height:300px; }
  /* Nivel 3 */
  details { margin-top:20px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 18px; }
  summary { cursor:pointer; font-size:14px; font-weight:600; }
  table { width:100%; border-collapse:collapse; font-size:13px; margin:10px 0 4px; }
  th, td { text-align:right; padding:6px 10px; border-bottom:1px solid var(--line); }
  th:first-child, td:first-child { text-align:left; }
  th { color:var(--muted); font-weight:600; }
  footer { font-size:12px; color:var(--muted); margin-top:16px; line-height:1.5; }
  @media (max-width: 900px) { .hero, .row2 { grid-template-columns:1fr; } .hero .big { font-size:52px; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <p class="eyebrow">Planeación de producción · semana del 18 al 25 de marzo de 2023 · 5 máquinas</p>
      <h1>Cumplimiento del programa de producción</h1>
    </div>
    <div class="filtro">
      <label for="op">Tipo de operación</label>
      <select id="op"></select>
    </div>
  </header>

  <!-- Nivel 1 · Vista general -->
  <section class="hero" aria-label="Resumen">
    <div>
      <div class="big" id="k-inc"></div>
      <div class="msg" id="msg"></div>
      <div class="sub" id="sub"></div>
    </div>
    <div class="kpis">
      <div class="kpi ret"><div class="v" id="k-ret"></div><div class="l">órdenes retrasadas (iniciaron 10–30 min tarde)</div></div>
      <div class="kpi acc"><div class="v" id="k-fal"></div><div class="l">órdenes fallidas (nunca iniciaron)</div></div>
      <div class="kpi acc"><div class="v" id="k-hfal"></div><div class="l" id="k-hfal-l"></div></div>
      <div class="kpi"><div class="v" id="k-n"></div><div class="l">órdenes programadas en el periodo</div></div>
    </div>
  </section>

  <!-- Nivel 2 · Tendencia y comparación -->
  <section class="row2">
    <div class="card">
      <h2 id="t-dia">Los retrasos subieron a mitad de semana</h2>
      <p class="note" id="n-dia"></p>
      <div id="g-dia" class="chart"></div>
    </div>
    <div class="card">
      <h2>Ninguna máquina explica el problema por sí sola</h2>
      <p class="note" id="n-maq"></p>
      <div id="g-maq" class="chart"></div>
    </div>
  </section>

  <!-- Nivel 3 · Detalle diagnóstico -->
  <details>
    <summary>Ver detalle por máquina</summary>
    <div style="overflow-x:auto"><table>
      <thead><tr><th>Máquina</th><th>Órdenes</th><th>Completadas</th><th>Retrasadas</th><th>Fallidas</th><th>Horas perdidas por fallas</th></tr></thead>
      <tbody id="tabla"></tbody>
    </table></div>
  </details>

  <footer>
    <b>Definiciones.</b> Incumplimiento = órdenes retrasadas + fallidas. Retrasada = inició de 10 a 30 min después de lo programado.
    Fallida = sin inicio real registrado. Horas perdidas = tiempo de proceso programado de las órdenes fallidas.
    Intervalos de confianza de Wilson al 95 %; diferencias entre máquinas evaluadas con prueba ji cuadrada.<br>
    <b>Limitaciones.</b> Una sola semana de datos, probablemente simulados; sin información de turnos, operadores ni causas de falla.
    Los sábados 18 y 25 son días incompletos.<br>
    Fuente: elaboración propia con datos de ziya07 (s.f.), <i>Manufacturing Production Data</i>, Kaggle. Generado con <code>src/dashboard_final.py</code>.
  </footer>
</div>

<script>
const DATA = __DATA__;
const C = {ret:"#E09A2B", fal:"#B8322A", neutral:"#9AA3AD", ink:"#1F2937", muted:"#6B7280", line:"#E5E7EB"};
const pct = (v, d=1) => (v*100).toFixed(d).replace(/\.0$/, "") + "\u00a0%";
const fmt = v => v.toLocaleString("es-MX", {maximumFractionDigits:0});
const cfg = {displayModeBar:false, responsive:true};
const base = {margin:{l:44, r:16, t:10, b:40}, paper_bgcolor:"#fff", plot_bgcolor:"#fff",
              font:{family:"Segoe UI, system-ui, Arial", size:12, color:C.ink},
              hoverlabel:{bgcolor:"#fff", bordercolor:"#CBD5E1", font:{size:12}}};

const sel = document.getElementById("op");
Object.keys(DATA).forEach(k => { const o = document.createElement("option"); o.textContent = k; sel.appendChild(o); });

function render(key) {
  const d = DATA[key];
  // Nivel 1
  document.getElementById("k-inc").textContent = pct(d.inc);
  document.getElementById("msg").textContent = "de las órdenes no se cumplió según el programa";
  document.getElementById("sub").innerHTML =
    `El problema está repartido en las 5 máquinas: sus diferencias caben dentro del margen de error. ` +
    `El patrón más visible es por día: de martes a jueves los retrasos llegaron a <b>${pct(d.ret_mid,0)}</b>, ` +
    `contra <b>${pct(d.ret_resto,0)}</b> el resto de la semana.`;
  document.getElementById("k-ret").textContent = pct(d.ret);
  document.getElementById("k-fal").textContent = pct(d.fal);
  document.getElementById("k-hfal").textContent = fmt(d.h_fal) + " h";
  document.getElementById("k-hfal-l").textContent =
    `de capacidad programada perdidas por fallas (${pct(d.h_fal/d.h_tot,0)} del total)`;
  document.getElementById("k-n").textContent = fmt(d.n);

  // Nivel 2a · retrasos por día (insight) con banda de mitad de semana
  const x = d.dias.map(r => r.etq + "<br><span style='color:#9CA3AF'>n=" + r.n + "</span>");
  const comp = d.dias.map(r => !r.parcial);
  const hover = (lab, k) => d.dias.map(r => `<b>${r.etq}</b>${r.parcial ? " (día parcial)" : ""}<br>${lab}: ${pct(r[k])}<br>Órdenes del día: ${r.n}`);
  const traces = [
    {x, y:d.dias.map(r => r.fal), mode:"lines+markers", name:"Fallidas",
     line:{color:C.neutral, width:1.5}, marker:{size:6, color:d.dias.map(r => r.parcial ? "#fff" : C.neutral), line:{color:C.neutral, width:1.5}},
     text:hover("Fallidas","fal"), hoverinfo:"text"},
    {x, y:d.dias.map(r => r.ret), mode:"lines+markers", name:"Retrasadas",
     line:{color:C.ret, width:3}, marker:{size:9, color:d.dias.map(r => r.parcial ? "#fff" : C.ret), line:{color:C.ret, width:2}},
     text:hover("Retrasadas","ret"), hoverinfo:"text"}
  ];
  const ymax = Math.max(0.35, ...d.dias.map(r => r.ret + 0.06));
  Plotly.react("g-dia", traces, {...base, showlegend:false,
    yaxis:{tickformat:".0%", range:[0, ymax], gridcolor:C.line, zeroline:false, title:{text:"% de las órdenes del día", font:{size:11, color:C.muted}}},
    xaxis:{tickfont:{size:11}, fixedrange:true},
    shapes:[{type:"rect", xref:"x", yref:"paper", x0:2.5, x1:5.5, y0:0, y1:1, fillcolor:"#FCEBD3", opacity:0.6, line:{width:0}, layer:"below"}],
    annotations:[
      {x:4, y:ymax*0.97, xref:"x", yref:"y", text:"<b>Mar 21 – Jue 23</b>", showarrow:false, font:{size:12, color:"#7A4A06"}},
      {x:7, y:d.dias[7].ret, xref:"x", yref:"y", text:"<b>Retrasadas</b>", xanchor:"left", xshift:10, showarrow:false, font:{color:C.ret}},
      {x:7, y:Math.max(d.dias[7].fal, 0.03), xref:"x", yref:"y", text:"Fallidas", xanchor:"left", xshift:10, showarrow:false, font:{color:C.muted}}],
    margin:{l:50, r:84, t:10, b:46}}, cfg);
  const nc = d.dias.filter(r => !r.parcial).map(r => r.n);
  const vol = Math.min(...nc) === Math.max(...nc)
    ? `Mismo volumen todos los días completos (${nc[0]} órdenes), así que no se explica por carga.`
    : `Días completos con ${Math.min(...nc)} a ${Math.max(...nc)} órdenes.`;
  document.getElementById("n-dia").textContent =
    vol + " Patrón de una sola semana: debe confirmarse con más datos. Marcadores huecos: sábados incompletos.";

  // Nivel 2b · máquinas con IC 95 % (todo en neutro: ninguna destaca)
  const m = [...d.maq].sort((a, b) => a.p - b.p);
  Plotly.react("g-maq", [
    {x:m.map(r => r.p), y:m.map(r => r.m), type:"scatter", mode:"markers", showlegend:false,
     error_x:{type:"data", symmetric:false, array:m.map(r => r.hi - r.p), arrayminus:m.map(r => r.p - r.lo), color:C.neutral, thickness:2, width:0},
     marker:{size:11, color:C.ink},
     text:m.map(r => `<b>${r.m}</b><br>Incumplimiento: ${pct(r.p)}<br>IC 95 %: ${pct(r.lo)} – ${pct(r.hi)}<br>Órdenes: ${r.n}`), hoverinfo:"text"}
  ], {...base,
    xaxis:{tickformat:".0%", range:[0, Math.max(0.6, ...m.map(r => r.hi + 0.05))], gridcolor:C.line, zeroline:false,
           title:{text:"% de órdenes retrasadas o fallidas (línea = IC 95 %)", font:{size:11, color:C.muted}}},
    yaxis:{fixedrange:true},
    shapes:[{type:"line", x0:d.inc, x1:d.inc, yref:"paper", y0:0, y1:1, line:{color:C.fal, width:1.5, dash:"dot"}}],
    annotations:[{x:d.inc, y:1.02, yref:"paper", text:"Promedio " + pct(d.inc), showarrow:false, font:{size:11, color:C.fal}, yanchor:"bottom"}],
    margin:{l:44, r:16, t:24, b:46}}, cfg);
  document.getElementById("n-maq").textContent = d.pval >= 0.05
    ? `Los intervalos se traslapan: las diferencias no son estadísticamente significativas (p = ${d.pval.toFixed(2)}).`
    : `Hay diferencias estadísticamente significativas entre máquinas (p = ${d.pval.toFixed(3)}).`;

  // Nivel 3 · tabla
  document.getElementById("tabla").innerHTML = d.tabla.map(r =>
    `<tr><td>${r.m}</td><td>${r.n}</td><td>${pct(r.comp)}</td><td>${pct(r.ret)}</td><td>${pct(r.fal)}</td><td>${r.hfal.toFixed(1)} h</td></tr>`).join("");
}
sel.addEventListener("change", e => render(e.target.value));
render(sel.value);
</script>
</body>
</html>
"""

html = (HTML.replace("__PLOTLY__", get_plotlyjs())
            .replace("__DATA__", json.dumps(DATA, ensure_ascii=False)))
OUT.write_text(html, encoding="utf-8")
t = DATA["Todas las operaciones"]
print(f"Dashboard generado: {OUT.relative_to(ROOT)}")
print(f"Incumplimiento {t['inc']:.1%} | retrasadas {t['ret']:.1%} | fallidas {t['fal']:.1%} | "
      f"horas perdidas {t['h_fal']:.1f} de {t['h_tot']:.1f} | p máquinas {t['pval']:.2f} | "
      f"retrasos mar–jue {t['ret_mid']:.1%} vs resto {t['ret_resto']:.1%}")
