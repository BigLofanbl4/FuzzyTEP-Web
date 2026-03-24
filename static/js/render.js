import { elements, getSelectedEnterprise, state } from "./dom.js";
import {
  escapeHtml,
  formatMoney,
  formatNumber,
  labelToCode,
  membershipKeyToHuman,
  membershipLabelToHuman,
  metricValueForMembership,
  profileToHuman,
  renderInsightCard,
} from "./utils.js";

export function updateDerivedPreview() {
  const revenue = Number(elements.analysisForm.revenue.value || 0);
  const profit = Number(elements.analysisForm.profit.value || 0);
  const costs = revenue > 0 ? revenue - profit : 0;
  const profitability = costs > 0 ? (profit / costs) * 100 : 0;

  elements.derivedCosts.textContent = costs > 0 ? formatMoney(costs) : "0";
  elements.derivedProfitability.textContent = costs > 0 ? `${formatNumber(profitability, 2)} %` : "0 %";
}

export function renderMemberships(result) {
  const memberships = result.memberships || {};
  const cards = Object.entries(memberships);

  if (!cards.length) {
    elements.membershipGrid.innerHTML = `
      <div class="empty-state">
        Для этого анализа карта принадлежности пока недоступна.
      </div>
    `;
    return;
  }

  elements.membershipGrid.innerHTML = cards
    .map(([metricKey, levels]) => {
      const dominant = Object.entries(levels).sort((a, b) => b[1] - a[1])[0];
      const rows = Object.entries(levels)
        .map(
          ([levelKey, value]) => `
            <div class="membership-row">
              <span>${membershipLabelToHuman(levelKey)}</span>
              <div class="membership-track">
                <div class="membership-fill ${levelKey}" style="width: ${Math.max(4, Number(value) * 100)}%"></div>
              </div>
              <span>${formatNumber(value, 3)}</span>
            </div>
          `
        )
        .join("");

      return `
        <article class="membership-card">
          <div class="membership-card-head">
            <strong>${membershipKeyToHuman(metricKey)}</strong>
            <span class="membership-value">${metricValueForMembership(result, metricKey)}</span>
          </div>
          <div class="membership-rows">${rows}</div>
          <div class="membership-best">
            Сейчас показатель ближе к уровню: <strong>${membershipLabelToHuman(dominant[0]).toLowerCase()}</strong>
          </div>
        </article>
      `;
    })
    .join("");
}

export function renderStats() {
  const analyses = state.enterprises.reduce((sum, item) => sum + Number(item.analyses_count || 0), 0);
  const scores = state.history.map((item) => Number(item.numeric_score || 0));
  const average = scores.length ? scores.reduce((sum, value) => sum + value, 0) / scores.length : 0;

  elements.statEnterprises.textContent = state.enterprises.length;
  elements.statAnalyses.textContent = analyses;
  elements.statAverage.textContent = average ? formatNumber(average) : "0";
}

export function renderEnterpriseList(onSelect) {
  if (!state.enterprises.length) {
    elements.enterpriseList.innerHTML = `
      <div class="empty-state">
        Пока нет предприятий. Нажмите "Новое", чтобы создать первую карточку.
      </div>
    `;
    return;
  }

  elements.enterpriseList.innerHTML = state.enterprises
    .map((item) => {
      const isActive = item.id === state.selectedEnterpriseId;
      const label = item.last_efficiency_label || "нет оценки";
      const code = labelToCode(label);

      return `
        <article class="enterprise-card ${isActive ? "active" : ""}" data-id="${item.id}">
          <h3>${escapeHtml(item.name)}</h3>
          <p class="muted">${escapeHtml(profileToHuman(item.profile_code))}</p>
          <div class="meta-row">
            <span class="tag ${item.last_efficiency_label ? code : ""}">${escapeHtml(label)}</span>
            <span class="tag">${item.analyses_count || 0} анализов</span>
          </div>
        </article>
      `;
    })
    .join("");

  elements.enterpriseList.querySelectorAll(".enterprise-card").forEach((card) => {
    card.addEventListener("click", () => onSelect(Number(card.dataset.id)));
  });
}

export function renderEnterpriseProfile() {
  const enterprise = getSelectedEnterprise();
  const hasEnterprise = Boolean(enterprise);

  elements.contentActions.hidden = !hasEnterprise;
  elements.profileEmpty.hidden = hasEnterprise;
  elements.profileContent.hidden = !hasEnterprise;

  if (!enterprise) {
    elements.enterpriseTitle.textContent = "Выберите предприятие";
    elements.enterpriseSubtitle.textContent =
      "После выбора здесь появятся данные предприятия, форма анализа и история результатов.";
    elements.historyEmpty.textContent = "История пока пуста.";
    elements.historyEmpty.hidden = false;
    elements.historyWrap.hidden = true;
    elements.resultPanel.hidden = !state.latestResult;
    return;
  }

  elements.enterpriseTitle.textContent = enterprise.name;
  elements.enterpriseSubtitle.textContent = `${profileToHuman(enterprise.profile_code)} · ${enterprise.ownership}`;
  elements.enterpriseProfile.textContent = profileToHuman(enterprise.profile_code);
  elements.enterpriseOwnership.textContent = enterprise.ownership;
  elements.enterpriseDescription.textContent = enterprise.description;
}

export function renderResult(result) {
  state.latestResult = result;
  if (!result) {
    elements.resultPanel.hidden = true;
    return;
  }

  const code = labelToCode(result.efficiency_label);
  elements.resultPanel.hidden = false;
  elements.resultBadge.textContent = result.efficiency_label;
  elements.resultBadge.className = `badge ${code}`;
  elements.resultScore.textContent = formatNumber(result.numeric_score);
  elements.resultTitle.textContent = `Итоговая оценка: ${result.efficiency_label}`;
  elements.resultComment.textContent = result.main_takeaway || result.comment;
  elements.resultExplanation.textContent = result.explanation;

  elements.modelSummary.innerHTML = [
    ["Главный вывод", result.main_takeaway || "нет данных"],
    ["Основной ориентир", result.actions?.[0] || "нет данных"],
    ["Профиль оценки", profileToHuman(result.industry_profile)],
  ]
    .map(
      ([label, value]) => `
        <div class="model-pill">
          <span>${label}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `
    )
    .join("");

  elements.resultMetrics.innerHTML = [
    ["Период", result.period],
    ["Выручка", formatMoney(result.revenue)],
    ["Прибыль", formatMoney(result.profit)],
    ["Затраты", `${formatMoney(result.costs)} (расчет)`],
    ["Рентабельность", `${formatNumber(result.profitability, 2)} %`],
    ["Маржа прибыли", `${formatNumber(result.profit_margin || (result.profit / result.revenue) * 100, 2)} %`],
    ["Доля затрат", `${formatNumber(result.cost_ratio || (result.costs / result.revenue) * 100, 2)} %`],
    ["Покрытие затрат", result.coverage_ratio ? formatNumber(result.coverage_ratio, 3) : "нет данных"],
    ["Темп роста выручки", `${formatNumber(result.revenue_growth, 2)} %`],
    ["Текущая ликвидность", formatNumber(result.liquidity_ratio, 2)],
  ]
    .map(
      ([label, value]) => `
        <div class="metric-card">
          <span>${label}</span>
          <strong>${value}</strong>
        </div>
      `
    )
    .join("");

  elements.decisionInsights.innerHTML = [
    renderInsightCard("Что поддерживает результат", result.strengths || [], "positive"),
    renderInsightCard("Что сдерживает оценку", result.risks || [], "warning"),
    renderInsightCard("Что проверить дальше", result.actions || [], "neutral"),
  ].join("");

  renderMemberships(result);

  elements.rulesList.innerHTML = result.triggered_rules?.length
    ? result.triggered_rules
        .map(
          (rule) => `
            <article class="rule-card">
              <strong>${escapeHtml(rule.name)}</strong>
              <p>${escapeHtml(rule.meaning)}</p>
              <p class="muted">Система увидела такую ситуацию: ${escapeHtml(rule.premise)}.</p>
              <p class="rule-impact">Влияние на итог: <strong>${escapeHtml(rule.impact)}</strong>.</p>
              <p class="muted">${escapeHtml(rule.action_hint)}</p>
            </article>
          `
        )
        .join("")
    : `
      <div class="empty-state">
        Для этого расчета не было одного ярко выраженного сценария, поэтому система опиралась на общий баланс показателей.
      </div>
    `;
}

export function renderHistory() {
  if (!state.history.length) {
    elements.historyEmpty.hidden = false;
    elements.historyWrap.hidden = true;
    return;
  }

  elements.historyEmpty.hidden = true;
  elements.historyWrap.hidden = false;
  elements.historyBody.innerHTML = state.history
    .map((item) => {
      const code = labelToCode(item.efficiency_label);
      return `
        <tr>
          <td>${new Date(item.created_at.replace(" ", "T")).toLocaleString("ru-RU")}</td>
          <td>${escapeHtml(item.period)}</td>
          <td><span class="badge ${code}">${escapeHtml(item.efficiency_label)}</span></td>
          <td>${formatNumber(item.numeric_score)}</td>
          <td>${escapeHtml(item.comment)}</td>
        </tr>
      `;
    })
    .join("");
}

export function syncFormAvailability() {
  const disabled = !state.selectedEnterpriseId;
  Array.from(elements.analysisForm.elements).forEach((field) => {
    field.disabled = disabled;
  });
  updateDerivedPreview();
}

export function openEnterpriseDialog(edit = false) {
  state.editMode = edit;
  const enterprise = getSelectedEnterprise();
  elements.dialogTitle.textContent = edit ? "Редактирование предприятия" : "Новое предприятие";
  elements.enterpriseForm.reset();
  elements.enterpriseForm.profile_code.value = "default";

  if (edit && enterprise) {
    elements.enterpriseForm.name.value = enterprise.name;
    elements.enterpriseForm.profile_code.value = enterprise.profile_code || "default";
    elements.enterpriseForm.ownership.value = enterprise.ownership;
    elements.enterpriseForm.description.value = enterprise.description;
  }

  elements.dialog.showModal();
}

export function closeEnterpriseDialog() {
  elements.dialog.close();
}
