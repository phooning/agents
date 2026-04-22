// ── MATH: BLACK-SCHOLES ──────────────────────────────────────────

function normCDF(x) {
  const a1 = 0.254829592,
    a2 = -0.284496736,
    a3 = 1.421413741,
    a4 = -1.453152027,
    a5 = 1.061405429,
    p = 0.3275911;
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x) / Math.sqrt(2);
  const t = 1 / (1 + p * x);
  const y =
    1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return 0.5 * (1 + sign * y);
}
function normPDF(x) {
  return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

function blackScholes(S, K, T, r, sigma, type) {
  if (T <= 0) {
    const intrinsic = type === "call" ? Math.max(0, S - K) : Math.max(0, K - S);
    return { price: intrinsic, d1: 0, d2: 0 };
  }
  const d1 =
    (Math.log(S / K) + (r + (sigma * sigma) / 2) * T) / (sigma * Math.sqrt(T));
  const d2 = d1 - sigma * Math.sqrt(T);
  let price;
  if (type === "call") {
    price = S * normCDF(d1) - K * Math.exp(-r * T) * normCDF(d2);
  } else {
    price = K * Math.exp(-r * T) * normCDF(-d2) - S * normCDF(-d1);
  }
  return { price: Math.max(0, price), d1, d2 };
}

function calcGreeks(S, K, T, r, sigma, type) {
  if (T <= 0)
    return {
      delta: type === "call" ? (S > K ? 1 : 0) : S < K ? -1 : 0,
      gamma: 0,
      theta: 0,
      vega: 0,
      rho: 0,
    };
  const { d1, d2 } = blackScholes(S, K, T, r, sigma, type);
  const sqrtT = Math.sqrt(T);
  const eRT = Math.exp(-r * T);

  const delta = type === "call" ? normCDF(d1) : normCDF(d1) - 1;
  const gamma = normPDF(d1) / (S * sigma * sqrtT);
  const vega = S * normPDF(d1) * sqrtT; // per 1.0 move in sigma
  let theta;
  if (type === "call") {
    theta =
      ((-S * normPDF(d1) * sigma) / (2 * sqrtT) - r * K * eRT * normCDF(d2)) /
      365;
  } else {
    theta =
      ((-S * normPDF(d1) * sigma) / (2 * sqrtT) + r * K * eRT * normCDF(-d2)) /
      365;
  }
  const rho =
    type === "call"
      ? (K * T * eRT * normCDF(d2)) / 100
      : (-K * T * eRT * normCDF(-d2)) / 100;

  return { delta, gamma, theta, vega: vega / 100, rho };
}

// ── STATE ──────────────────────────────────────────────────────
let optionType = "call";
function setType(t, btn) {
  optionType = t;
  document
    .querySelectorAll(".type-btn")
    .forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  updateSim();
}

function getParams() {
  return {
    S: +document.getElementById("stockPrice").value,
    K: +document.getElementById("strikePrice").value,
    T: +document.getElementById("timeExpiry").value / 365,
    r: +document.getElementById("riskFree").value / 100,
    sigma: +document.getElementById("volatility").value / 100,
    days: +document.getElementById("timeExpiry").value,
  };
}

// ── CANVAS CHART ───────────────────────────────────────────────
const canvas = document.getElementById("payoffChart");
const ctx = canvas.getContext("2d");

function drawChart(S, K, premium, type) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const W = rect.width,
    H = rect.height;
  const pad = { l: 60, r: 30, t: 24, b: 44 };
  const chartW = W - pad.l - pad.r;
  const chartH = H - pad.t - pad.b;

  // Price range for x-axis
  const sMin = Math.max(5, Math.round(Math.min(S, K) * 0.6));
  const sMax = Math.round(Math.max(S, K) * 1.45);

  // Compute payoffs
  const pts = [];
  for (let i = 0; i <= 200; i++) {
    const price = sMin + (sMax - sMin) * (i / 200);
    let pnl;
    if (type === "call") {
      pnl = (Math.max(0, price - K) - premium) * 100;
    } else {
      pnl = (Math.max(0, K - price) - premium) * 100;
    }
    pts.push({ price, pnl });
  }

  // PnL range
  const maxPnl = Math.max(...pts.map((p) => p.pnl));
  const minPnl = Math.min(...pts.map((p) => p.pnl));
  const yPad = Math.max(Math.abs(maxPnl), Math.abs(minPnl)) * 0.15;
  const yMax = maxPnl + yPad;
  const yMin = minPnl - yPad;
  const yRange = yMax - yMin;

  const xScale = (p) => pad.l + ((p - sMin) / (sMax - sMin)) * chartW;
  const yScale = (v) => pad.t + (1 - (v - yMin) / yRange) * chartH;

  // ── BACKGROUND
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, W, H);

  // ── GRID
  ctx.strokeStyle = "rgba(0,0,0,0.045)";
  ctx.lineWidth = 1;
  const yTicks = 6;
  for (let i = 0; i <= yTicks; i++) {
    const v = yMin + (yRange * i) / yTicks;
    const y = yScale(v);
    ctx.beginPath();
    ctx.moveTo(pad.l, y);
    ctx.lineTo(W - pad.r, y);
    ctx.stroke();

    ctx.fillStyle = "rgba(0,0,0,0.3)";
    ctx.font = `${9.5 / dpr + 9.5}px DM Mono, monospace`; // hack; just set px
    ctx.font = "10px DM Mono, monospace";
    ctx.textAlign = "right";
    const label =
      Math.abs(v) < 1
        ? "$0"
        : (v > 0 ? "+$" : "-$") + Math.round(Math.abs(v)).toLocaleString();
    ctx.fillText(label, pad.l - 6, y + 3.5);
  }

  const xTicks = 8;
  for (let i = 0; i <= xTicks; i++) {
    const p = sMin + ((sMax - sMin) * i) / xTicks;
    const x = xScale(p);
    ctx.beginPath();
    ctx.moveTo(x, pad.t);
    ctx.lineTo(x, H - pad.b);
    ctx.stroke();
    ctx.fillStyle = "rgba(0,0,0,0.3)";
    ctx.textAlign = "center";
    ctx.font = "10px DM Mono, monospace";
    ctx.fillText("$" + Math.round(p), x, H - pad.b + 14);
  }

  // ── ZERO LINE
  const y0 = yScale(0);
  ctx.strokeStyle = "rgba(0,0,0,0.18)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 3]);
  ctx.beginPath();
  ctx.moveTo(pad.l, y0);
  ctx.lineTo(W - pad.r, y0);
  ctx.stroke();
  ctx.setLineDash([]);

  // ── FILLED AREA ABOVE / BELOW
  // Profit area
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(xScale(pts[0].price), y0);
  pts.forEach((p) => ctx.lineTo(xScale(p.price), yScale(Math.max(0, p.pnl))));
  ctx.lineTo(xScale(pts[pts.length - 1].price), y0);
  ctx.closePath();
  ctx.fillStyle = "rgba(26, 107, 60, 0.12)";
  ctx.fill();
  ctx.restore();

  // Loss area
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(xScale(pts[0].price), y0);
  pts.forEach((p) => ctx.lineTo(xScale(p.price), yScale(Math.min(0, p.pnl))));
  ctx.lineTo(xScale(pts[pts.length - 1].price), y0);
  ctx.closePath();
  ctx.fillStyle = "rgba(139, 26, 26, 0.10)";
  ctx.fill();
  ctx.restore();

  // ── PAYOFF LINE
  ctx.strokeStyle = type === "call" ? "#1a6b3c" : "#8b1a1a";
  ctx.lineWidth = 2.5;
  ctx.lineJoin = "round";
  ctx.beginPath();
  pts.forEach((p, i) => {
    if (i === 0) ctx.moveTo(xScale(p.price), yScale(p.pnl));
    else ctx.lineTo(xScale(p.price), yScale(p.pnl));
  });
  ctx.stroke();

  // ── BREAKEVEN MARKER
  const breakeven = type === "call" ? K + premium : K - premium;
  if (breakeven >= sMin && breakeven <= sMax) {
    const bx = xScale(breakeven);
    ctx.strokeStyle = "#b8932a";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 3]);
    ctx.beginPath();
    ctx.moveTo(bx, pad.t);
    ctx.lineTo(bx, H - pad.b);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "#b8932a";
    ctx.font = "bold 10px DM Mono, monospace";
    ctx.textAlign = "center";
    ctx.fillText("BE $" + breakeven.toFixed(1), bx, pad.t - 8);
  }

  // ── CURRENT STOCK PRICE MARKER
  if (S >= sMin && S <= sMax) {
    const sx = xScale(S);
    ctx.strokeStyle = "rgba(0,0,0,0.25)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([2, 2]);
    ctx.beginPath();
    ctx.moveTo(sx, pad.t);
    ctx.lineTo(sx, H - pad.b);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.font = "10px DM Mono, monospace";
    ctx.textAlign = "center";
    ctx.fillText("S $" + S, sx, pad.t - 8);
  }

  // ── AXIS LABEL
  ctx.fillStyle = "rgba(0,0,0,0.3)";
  ctx.font = "9px DM Mono, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Stock Price at Expiration", pad.l + chartW / 2, H - 4);
}

// ── MAIN UPDATE ────────────────────────────────────────────────
function updateSim() {
  const { S, K, T, r, sigma, days } = getParams();

  // Update labels
  document.getElementById("sVal").textContent = "$" + S;
  document.getElementById("kVal").textContent = "$" + K;
  document.getElementById("tVal").textContent =
    days + " day" + (days !== 1 ? "s" : "");
  document.getElementById("vVal").textContent = Math.round(sigma * 100) + "%";
  document.getElementById("rVal").textContent = (r * 100).toFixed(1) + "%";

  // Black-Scholes
  const bs = blackScholes(S, K, T, r, sigma, optionType);
  const premium = bs.price;
  const contractCost = premium * 100;
  const breakeven = optionType === "call" ? K + premium : K - premium;

  // Metrics
  document.getElementById("metPremium").textContent = "$" + premium.toFixed(2);
  document.getElementById("metContract").textContent =
    "$" + contractCost.toFixed(0);
  document.getElementById("metBreakeven").textContent =
    "$" + breakeven.toFixed(2);
  document.getElementById("metMaxLoss").textContent =
    "−$" + contractCost.toFixed(0);

  // Greeks
  const g = calcGreeks(S, K, T, r, sigma, optionType);
  document.getElementById("gDelta").textContent = g.delta.toFixed(3);
  document.getElementById("gGamma").textContent = g.gamma.toFixed(4);
  document.getElementById("gTheta").textContent =
    (g.theta * 100).toFixed(2) + "¢/day";
  document.getElementById("gVega").textContent =
    "$" + (g.vega * 100).toFixed(2);
  document.getElementById("gRho").textContent = "$" + (g.rho * 100).toFixed(3);

  // Color code delta
  const dEl = document.getElementById("gDelta");
  dEl.style.color =
    g.delta > 0.5 ? "var(--profit)" : g.delta < 0 ? "var(--loss)" : "inherit";

  // Chart
  drawChart(S, K, premium, optionType);
}

// ── INIT + RESIZE ──────────────────────────────────────────────
window.addEventListener("resize", () => updateSim());
updateSim();
