export const state = {
  enterprises: [],
  history: [],
  selectedEnterpriseId: null,
  latestResult: null,
  editMode: false,
};

export const elements = {
  enterpriseList: document.getElementById("enterprise-list"),
  enterpriseTitle: document.getElementById("enterprise-title"),
  enterpriseSubtitle: document.getElementById("enterprise-subtitle"),
  enterpriseProfile: document.getElementById("enterprise-profile"),
  enterpriseOwnership: document.getElementById("enterprise-ownership"),
  enterpriseDescription: document.getElementById("enterprise-description"),
  profileEmpty: document.getElementById("profile-empty"),
  profileContent: document.getElementById("profile-content"),
  analysisForm: document.getElementById("analysis-form"),
  derivedCosts: document.getElementById("derived-costs"),
  derivedProfitability: document.getElementById("derived-profitability"),
  resultPanel: document.getElementById("result-panel"),
  resultBadge: document.getElementById("result-badge"),
  modelSummary: document.getElementById("model-summary"),
  resultScore: document.getElementById("result-score"),
  resultTitle: document.getElementById("result-title"),
  resultComment: document.getElementById("result-comment"),
  resultExplanation: document.getElementById("result-explanation"),
  resultMetrics: document.getElementById("result-metrics"),
  decisionInsights: document.getElementById("decision-insights"),
  membershipGrid: document.getElementById("membership-grid"),
  rulesList: document.getElementById("rules-list"),
  historyBody: document.getElementById("history-body"),
  historyEmpty: document.getElementById("history-empty"),
  historyWrap: document.getElementById("history-wrap"),
  statEnterprises: document.getElementById("stat-enterprises"),
  statAnalyses: document.getElementById("stat-analyses"),
  statAverage: document.getElementById("stat-average"),
  dialog: document.getElementById("enterprise-dialog"),
  dialogTitle: document.getElementById("dialog-title"),
  enterpriseForm: document.getElementById("enterprise-form"),
  contentActions: document.getElementById("content-actions"),
  toast: document.getElementById("toast"),
};

export function getSelectedEnterprise() {
  return state.enterprises.find((item) => item.id === state.selectedEnterpriseId) || null;
}
