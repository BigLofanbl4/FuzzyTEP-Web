import { elements } from "./dom.js";

export function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => {
    elements.toast.hidden = true;
  }, 3400);
}

export function formatMoney(value) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

export function formatNumber(value, digits = 1) {
  return new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(Number(value || 0));
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function labelToCode(label) {
  const map = {
    низкая: "low",
    удовлетворительная: "satisfactory",
    хорошая: "good",
    высокая: "high",
  };
  return map[label] || "good";
}

export function profileToHuman(profile) {
  const map = {
    manufacturing: "производство / машиностроение",
    trade: "торговля",
    services: "услуги / IT / сервис",
    default: "универсальный профиль",
  };
  return map[profile] || "универсальный профиль";
}

export function membershipLabelToHuman(label) {
  const map = {
    low: "Низкий",
    medium: "Средний",
    high: "Высокий",
  };
  return map[label] || label;
}

export function membershipKeyToHuman(key) {
  const map = {
    profit_margin: "Маржа прибыли",
    cost_ratio: "Доля затрат",
    profitability: "Рентабельность",
    coverage: "Покрытие затрат",
    growth: "Темп роста выручки",
    liquidity: "Текущая ликвидность",
  };
  return map[key] || key;
}

export function metricValueForMembership(result, key) {
  const map = {
    profit_margin: `${formatNumber(result.profit_margin, 2)} %`,
    cost_ratio: `${formatNumber(result.cost_ratio, 2)} %`,
    profitability: `${formatNumber(result.profitability, 2)} %`,
    coverage: formatNumber(result.coverage_ratio, 3),
    growth: `${formatNumber(result.revenue_growth, 2)} %`,
    liquidity: formatNumber(result.liquidity_ratio, 2),
  };
  return map[key] || "нет данных";
}

export function renderInsightCard(title, items, tone = "") {
  const rows = (items || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");

  return `
    <article class="insight-card ${tone}">
      <h4>${escapeHtml(title)}</h4>
      <ul class="insight-list">${rows}</ul>
    </article>
  `;
}
