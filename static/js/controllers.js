import { api } from "./api.js";
import { elements, getSelectedEnterprise, state } from "./dom.js";
import {
  closeEnterpriseDialog,
  openEnterpriseDialog,
  renderEnterpriseList,
  renderEnterpriseProfile,
  renderHistory,
  renderResult,
  renderStats,
  syncFormAvailability,
  updateDerivedPreview,
} from "./render.js";
import { showToast } from "./utils.js";

export async function loadEnterprises(selectId = null) {
  const data = await api("/api/enterprises");
  state.enterprises = data.items;

  if (selectId) {
    state.selectedEnterpriseId = selectId;
  } else if (!state.selectedEnterpriseId && state.enterprises.length) {
    state.selectedEnterpriseId = state.enterprises[0].id;
  } else if (
    state.selectedEnterpriseId &&
    !state.enterprises.some((item) => item.id === state.selectedEnterpriseId)
  ) {
    state.selectedEnterpriseId = state.enterprises[0]?.id || null;
  }

  renderEnterpriseList(selectEnterprise);
  renderEnterpriseProfile();
  renderStats();
  syncFormAvailability();

  if (state.selectedEnterpriseId) {
    await loadHistory(state.selectedEnterpriseId);
  } else {
    state.history = [];
    renderHistory();
    renderResult(null);
  }
}

export async function loadHistory(enterpriseId) {
  const data = await api(`/api/enterprises/${enterpriseId}/history`);
  state.history = data.items;
  renderHistory();
  renderStats();
  renderResult(state.history[0] || null);
}

export async function selectEnterprise(enterpriseId) {
  state.selectedEnterpriseId = enterpriseId;
  renderEnterpriseList(selectEnterprise);
  renderEnterpriseProfile();
  syncFormAvailability();
  await loadHistory(enterpriseId);
}

async function createOrUpdateEnterprise(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(elements.enterpriseForm).entries());
  const method = state.editMode ? "PUT" : "POST";
  const path = state.editMode ? `/api/enterprises/${state.selectedEnterpriseId}` : "/api/enterprises";

  try {
    const data = await api(path, { method, body: JSON.stringify(payload) });
    closeEnterpriseDialog();
    await loadEnterprises(data.item.id);
    showToast(state.editMode ? "Предприятие обновлено." : "Предприятие создано.");
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteEnterprise() {
  const enterprise = getSelectedEnterprise();
  if (!enterprise) {
    return;
  }

  const confirmed = window.confirm(`Удалить предприятие "${enterprise.name}" вместе с историей анализов?`);
  if (!confirmed) {
    return;
  }

  try {
    await api(`/api/enterprises/${enterprise.id}`, { method: "DELETE" });
    state.selectedEnterpriseId = null;
    await loadEnterprises();
    showToast("Предприятие удалено.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitAnalysis(event) {
  event.preventDefault();
  if (!state.selectedEnterpriseId) {
    showToast("Сначала выберите предприятие.");
    return;
  }

  const raw = Object.fromEntries(new FormData(elements.analysisForm).entries());
  const payload = {
    ...raw,
    revenue: Number(raw.revenue),
    profit: Number(raw.profit),
    revenue_growth: Number(raw.revenue_growth),
    liquidity_ratio: Number(raw.liquidity_ratio),
  };

  try {
    const data = await api(`/api/enterprises/${state.selectedEnterpriseId}/analyze`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await loadEnterprises(state.selectedEnterpriseId);
    renderResult(data.item);
    showToast("Анализ успешно выполнен и сохранен в истории.");
  } catch (error) {
    showToast(error.message);
  }
}

function setInitialPeriod() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  elements.analysisForm.period.value = `${now.getFullYear()}-${month}`;
  elements.analysisForm.revenue_growth.value = "0";
  elements.analysisForm.liquidity_ratio.value = "1.20";
  updateDerivedPreview();
}

function bindEvents() {
  document.getElementById("create-enterprise-trigger").addEventListener("click", () => openEnterpriseDialog(false));
  document.getElementById("sidebar-create-trigger").addEventListener("click", () => openEnterpriseDialog(false));
  document.getElementById("edit-enterprise-trigger").addEventListener("click", () => openEnterpriseDialog(true));
  document.getElementById("delete-enterprise-trigger").addEventListener("click", deleteEnterprise);
  document.getElementById("close-dialog").addEventListener("click", closeEnterpriseDialog);
  document.getElementById("cancel-dialog").addEventListener("click", closeEnterpriseDialog);
  elements.enterpriseForm.addEventListener("submit", createOrUpdateEnterprise);
  elements.analysisForm.addEventListener("submit", submitAnalysis);
  ["revenue", "profit"].forEach((name) => {
    elements.analysisForm[name].addEventListener("input", updateDerivedPreview);
  });
}

export async function initApp() {
  bindEvents();
  setInitialPeriod();
  syncFormAvailability();

  try {
    await loadEnterprises();
  } catch (error) {
    showToast(error.message);
  }
}
