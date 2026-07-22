"use strict";

const params = new URLSearchParams(window.location.search);
const incomingToken = params.get("token");
if (incomingToken) {
  sessionStorage.setItem("aiconfig-token", incomingToken);
  history.replaceState({}, "", window.location.pathname);
}
const token = sessionStorage.getItem("aiconfig-token") || "";

const ui = {
  summary: document.querySelector("#summary"),
  outputPath: document.querySelector("#output-path"),
  outputState: document.querySelector("#output-state"),
  visibleCount: document.querySelector("#visible-count"),
  itemList: document.querySelector("#item-list"),
  search: document.querySelector("#search"),
  targetFilter: document.querySelector("#target-filter"),
  statusFilter: document.querySelector("#status-filter"),
  emptyDetail: document.querySelector("#empty-detail"),
  detailContent: document.querySelector("#detail-content"),
  detailTarget: document.querySelector("#detail-target"),
  detailStatus: document.querySelector("#detail-status"),
  detailPath: document.querySelector("#detail-path"),
  sourceCount: document.querySelector("#source-count"),
  candidateList: document.querySelector("#candidate-list"),
  docsContent: document.querySelector("#docs-content"),
  docsFreshness: document.querySelector("#docs-freshness"),
  decisionSelect: document.querySelector("#decision-select"),
  decisionHint: document.querySelector("#decision-hint"),
  manualValue: document.querySelector("#manual-value"),
  saveDecision: document.querySelector("#save-decision"),
  previewMessage: document.querySelector("#preview-message"),
  preview: document.querySelector("#preview code"),
  generate: document.querySelector("#generate"),
  download: document.querySelector("#download-preview"),
  toast: document.querySelector("#toast"),
};

const app = { snapshot: null, items: [], selectedKey: null, preview: null, previewKind: "facts", toastTimer: null };
const labels = {
  unique: "唯一",
  duplicate: "重复",
  conflict: "冲突",
  sensitive: "敏感字段",
  "out-of-scope": "范围外",
  excluded: "已剔除",
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Aiconfig-Token": token, ...(options.headers || {}) },
  });
  let value;
  try { value = await response.json(); } catch { value = {}; }
  if (!response.ok) {
    const error = new Error(value.error?.message || `请求失败（${response.status}）`);
    error.code = value.error?.code;
    error.location = value.error?.location;
    throw error;
  }
  return value;
}

function notify(message, isError = false) {
  clearTimeout(app.toastTimer);
  ui.toast.textContent = message;
  ui.toast.className = `toast${isError ? " error" : ""}`;
  ui.toast.hidden = false;
  app.toastTimer = setTimeout(() => { ui.toast.hidden = true; }, 3800);
}

function normalizedStatus(item) {
  if (item.action === "exclude") return "excluded";
  if (["sensitive", "out-of-scope"].includes(item.status)) return "protected";
  return item.status;
}

function allItems(snapshot) {
  const result = [];
  for (const [target, targetPlan] of Object.entries(snapshot.plan.targets)) {
    for (const item of targetPlan.items || []) {
      result.push({ ...item, target, key: `${target}:${item.path}` });
    }
  }
  return result;
}

function renderSummary() {
  const values = [
    [app.snapshot.summary.total, "配置项", ""],
    [app.snapshot.summary.duplicates, "已去重", "warning"],
    [app.snapshot.summary.unresolved, "待解决冲突", app.snapshot.summary.unresolved ? "danger" : ""],
    [app.snapshot.summary.excluded, "已剔除", ""],
  ];
  ui.summary.replaceChildren(...values.map(([count, label, kind]) => {
    const card = element("div", `metric ${kind}`.trim());
    card.append(element("strong", "", String(count)), element("span", "", label));
    return card;
  }));
  ui.outputPath.textContent = app.snapshot.outputPath;
  ui.outputState.textContent = app.snapshot.outputExists ? "文件已存在" : "尚未生成";
  ui.outputState.className = `pill ${app.snapshot.outputExists ? "duplicate" : "neutral"}`;
}

function renderList() {
  const query = ui.search.value.trim().toLowerCase();
  const target = ui.targetFilter.value;
  const status = ui.statusFilter.value;
  const visible = app.items.filter((item) => {
    const haystack = `${item.path} ${item.target} ${(item.sources || []).join(" ")}`.toLowerCase();
    return (!query || haystack.includes(query))
      && (target === "all" || item.target === target)
      && (status === "all" || normalizedStatus(item) === status);
  });
  ui.visibleCount.textContent = `${visible.length} / ${app.items.length}`;
  const nodes = visible.map((item) => {
    const statusName = normalizedStatus(item);
    const button = element("button", `item-row${item.key === app.selectedKey ? " selected" : ""}`);
    button.type = "button";
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", item.key === app.selectedKey ? "true" : "false");
    button.addEventListener("click", () => selectItem(item.key));
    const dot = element("span", `status-dot ${statusName}`);
    const main = element("span", "item-main");
    main.append(element("span", "item-path", item.path || "/"));
    const sourceCount = item.candidates ? item.candidates.flatMap((entry) => entry.sources || []).length : (item.sources || []).length;
    main.append(element("span", "item-meta", `${sourceCount} 个来源 · ${labels[item.status] || item.status}`));
    button.append(dot, main, element("span", "target-tag", item.target));
    return button;
  });
  if (!nodes.length) nodes.push(element("p", "empty-state", "没有匹配的配置项。"));
  ui.itemList.replaceChildren(...nodes);
}

function formatValue(value) {
  if (typeof value === "string") return JSON.stringify(value);
  if (value === undefined) return "（无值）";
  return JSON.stringify(value, null, 2);
}

function currentItem() {
  return app.items.find((item) => item.key === app.selectedKey) || null;
}

function addDecisionOption(value, text) {
  const option = element("option", "", text);
  option.value = value;
  ui.decisionSelect.append(option);
}

function renderDecision(item) {
  ui.decisionSelect.replaceChildren();
  const protectedItem = ["sensitive", "out-of-scope"].includes(item.status);
  if (protectedItem) {
    addDecisionOption("exclude", "剔除（强制保护）");
    ui.decisionSelect.disabled = true;
    ui.saveDecision.disabled = true;
    ui.decisionHint.textContent = item.status === "sensitive" ? "检测到疑似秘密，此项不会写入事实文件。" : "该字段不属于受管理配置文件范围。";
  } else {
    ui.decisionSelect.disabled = false;
    ui.saveDecision.disabled = false;
    if (item.status === "conflict") {
      addDecisionOption("unresolved", "暂不处理");
      for (const candidate of item.candidates || []) {
        for (const source of candidate.sources || []) addDecisionOption(`take:${source}`, `采用 ${source}`);
      }
      const canUnion = (item.candidates || []).length > 0 && item.candidates.every((candidate) => Array.isArray(candidate.value));
      if (canUnion) addDecisionOption("union", "合并数组并去重");
      addDecisionOption("set", "手动设置值");
      addDecisionOption("exclude", "剔除此项");
      ui.decisionHint.textContent = "冲突项必须选择一个来源、合并数组、手动设置或剔除。";
    } else {
      addDecisionOption("keep", "保留");
      addDecisionOption("set", "手动设置值");
      addDecisionOption("exclude", "剔除此项");
      ui.decisionHint.textContent = item.status === "duplicate" ? "多个来源值一致，已自动去重。" : "该值仅出现在一个来源中。";
    }
    if (item.action === "take") ui.decisionSelect.value = `take:${item.source}`;
    else ui.decisionSelect.value = item.action || "unresolved";
  }
  ui.manualValue.hidden = ui.decisionSelect.value !== "set";
  ui.manualValue.value = item.selectedValue === undefined ? "" : formatValue(item.selectedValue);
}

function renderDetail(item) {
  ui.emptyDetail.hidden = true;
  ui.detailContent.hidden = false;
  ui.detailTarget.textContent = item.target;
  ui.detailStatus.textContent = labels[item.status] || item.status;
  ui.detailStatus.className = `pill ${normalizedStatus(item)}`;
  ui.detailPath.textContent = item.path || "/";
  const candidates = item.candidates || [{ sources: item.sources || [], value: item.value }];
  ui.sourceCount.textContent = `${candidates.flatMap((entry) => entry.sources || []).length} 个来源`;
  ui.candidateList.replaceChildren(...candidates.map((candidate) => {
    const card = element("article", "candidate");
    card.append(element("div", "candidate-label", (candidate.sources || []).join(" · ")));
    const pre = element("pre");
    pre.append(element("code", "", formatValue(candidate.value)));
    card.append(pre);
    return card;
  }));
  renderDecision(item);
}

async function loadDocs(refresh = false) {
  const item = currentItem();
  if (!item) return;
  const key = item.key;
  ui.docsFreshness.textContent = "查询中";
  ui.docsFreshness.className = "pill neutral";
  ui.docsContent.replaceChildren(element("p", "muted", "正在读取官方 Schema…"));
  try {
    const query = new URLSearchParams({ target: item.target, path: item.path, refresh: refresh ? "1" : "0" });
    const docs = await api(`/api/docs?${query}`);
    if (currentItem()?.key !== key) return;
    ui.docsFreshness.textContent = docs.stale ? "离线缓存" : "Schema 缓存";
    ui.docsFreshness.className = `pill ${docs.stale ? "duplicate" : ""}`;
    const content = document.createDocumentFragment();
    content.append(element("p", "", docs.description || "官方 Schema 暂未提供此配置项的说明。"));
    const meta = element("dl", "docs-meta");
    const rows = [
      ["类型", docs.type || "未声明"],
      ["允许值", docs.allowedValues?.length ? docs.allowedValues.join(", ") : "未声明"],
      ["默认值", docs.default === undefined || docs.default === null ? "未声明" : formatValue(docs.default)],
      ["缓存时间", docs.fetchedAt || "未知"],
    ];
    for (const [name, value] of rows) meta.append(element("dt", "", name), element("dd", "", value));
    content.append(meta);
    const link = element("a", "", "打开来源 Schema ↗");
    link.href = docs.sourceUrl;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    content.append(link);
    ui.docsContent.replaceChildren(content);
  } catch (error) {
    ui.docsFreshness.textContent = "查询失败";
    ui.docsFreshness.className = "pill conflict";
    ui.docsContent.replaceChildren(element("p", "muted", error.message));
  }
}

function selectItem(key) {
  app.selectedKey = key;
  renderList();
  const item = currentItem();
  if (item) {
    renderDetail(item);
    loadDocs(false);
  }
}

function decisionPayload() {
  const value = ui.decisionSelect.value;
  if (value.startsWith("take:")) return { action: "take", source: value.slice(5) };
  if (value === "set") {
    const raw = ui.manualValue.value;
    if (!raw.trim()) throw new Error("手动值不能为空。");
    try { return { action: "set", selectedValue: JSON.parse(raw) }; }
    catch { return { action: "set", selectedValue: raw }; }
  }
  return { action: value };
}

async function saveDecision() {
  const item = currentItem();
  if (!item) return;
  try {
    const snapshot = await api("/api/decision", {
      method: "POST",
      body: JSON.stringify({ target: item.target, path: item.path, decision: decisionPayload() }),
    });
    app.snapshot = snapshot;
    app.items = allItems(snapshot);
    renderSummary();
    renderList();
    const updated = currentItem();
    if (updated) renderDetail(updated);
    await refreshPreview();
    notify("决策已写入导入计划。");
  } catch (error) { notify(error.message, true); }
}

function renderPreview() {
  const content = app.preview?.[app.previewKind];
  ui.preview.textContent = content || `当前计划没有 ${app.previewKind} 输出。`;
  document.querySelectorAll("[data-preview]").forEach((button) => {
    button.classList.toggle("active", button.dataset.preview === app.previewKind);
  });
  ui.download.disabled = !content;
}

async function refreshPreview() {
  if (app.snapshot.summary.unresolved) {
    app.preview = null;
    ui.previewMessage.textContent = `仍有 ${app.snapshot.summary.unresolved} 项冲突待处理。`;
    ui.preview.textContent = "解决全部冲突后，这里会显示事实文件与目标配置预览。";
    ui.generate.disabled = true;
    ui.download.disabled = true;
    return;
  }
  try {
    app.preview = await api("/api/preview");
    ui.previewMessage.textContent = app.preview.warnings?.length ? app.preview.warnings.join("；") : "预览已通过结构与输出校验。";
    ui.generate.disabled = false;
    renderPreview();
  } catch (error) {
    app.preview = null;
    ui.previewMessage.textContent = error.message;
    ui.preview.textContent = "预览生成失败。";
    ui.generate.disabled = true;
  }
}

async function loadState() {
  try {
    app.snapshot = await api("/api/state");
    app.items = allItems(app.snapshot);
    renderSummary();
    renderList();
    if (app.selectedKey && currentItem()) renderDetail(currentItem());
    await refreshPreview();
  } catch (error) {
    notify(token ? error.message : "会话令牌缺失，请从 aiconfig ui 输出的网址重新打开。", true);
  }
}

async function generate(force = false) {
  try {
    const result = await api("/api/generate", { method: "POST", body: JSON.stringify({ force }) });
    notify(result.backup ? `事实文件已生成，旧文件备份至 ${result.backup}` : `事实文件已生成：${result.path}`);
    await loadState();
  } catch (error) {
    if (error.code === "IMPORT_OUTPUT_EXISTS" && !force) {
      const confirmed = window.confirm("事实文件已存在。继续将先创建备份，再覆盖原文件。是否继续？");
      if (confirmed) await generate(true);
      return;
    }
    notify(error.message, true);
  }
}

ui.search.addEventListener("input", renderList);
ui.targetFilter.addEventListener("change", renderList);
ui.statusFilter.addEventListener("change", renderList);
ui.decisionSelect.addEventListener("change", () => { ui.manualValue.hidden = ui.decisionSelect.value !== "set"; });
ui.saveDecision.addEventListener("click", saveDecision);
document.querySelector("#refresh-docs").addEventListener("click", () => loadDocs(true));
document.querySelector("#refresh-state").addEventListener("click", loadState);
ui.generate.addEventListener("click", () => generate(false));
ui.download.addEventListener("click", () => {
  const content = app.preview?.[app.previewKind];
  if (!content) return;
  const names = { facts: "agent-config.yaml", codex: "config.toml", claude: "settings.json" };
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([content], { type: "text/plain;charset=utf-8" }));
  link.download = names[app.previewKind];
  link.click();
  URL.revokeObjectURL(link.href);
});
document.querySelectorAll("[data-preview]").forEach((button) => {
  button.addEventListener("click", () => { app.previewKind = button.dataset.preview; renderPreview(); });
});

loadState();
