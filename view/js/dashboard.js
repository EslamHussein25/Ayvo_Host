// Model and file mapping
const modelTabs = [
  { label: "GPT-4o", key: "gpt-4o" },
  { label: "DeepSeek Chat", key: "DeepSeek Chat" },
  { label: "Claude3.7", key: "Claude3.7" },
  { label: "Gemini2.5Pro", key: "Gemini2.5Pro" },
  { label: "Grok3", key: "Grok3" }
];
const modelFiles = {
  "gpt-4o": "../../outputFiles/gpt-4o_evaluation_results.xlsx",
  "DeepSeek Chat": "../../outputFiles/deepseek chat_evaluation_results.xlsx",
  "Claude3.7": "../../outputFiles//claude3.7_evaluation_results.xlsx",
  "Gemini2.5Pro": "../../outputFiles//gemini2.5pro_evaluation_results.xlsx",
  "Grok3": "../../outputFiles//grok3_evaluation_results.xlsx"
};
const subTabs = [
  { label: "Current Result", key: "current" },
  { label: "Category Analysis", key: "category" }
];

// Render table from XLSX
function renderTable(model, sheetName, elementId) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element ${elementId} not found`);
    return;
  }
  
  if (!modelFiles[model]) {
    element.innerHTML = "<p>No data found.</p>";
    return;
  }
  
  console.log(`Loading ${sheetName} for ${model} into ${elementId}`);
  
  fetch(modelFiles[model])
    .then(res => res.arrayBuffer())
    .then(data => {
      const workbook = XLSX.read(data);
      const sheet = workbook.Sheets[sheetName];
      if (!sheet) {
        element.innerHTML = `<p>Sheet '${sheetName}' not found.</p>`;
        return;
      }
      const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });
      if (!json.length) {
        element.innerHTML = "<p>No data found.</p>";
        return;
      }
      let html = "<table><thead><tr>";
      Object.keys(json[0]).forEach(col => { html += `<th>${col}</th>`; });
      html += "</tr></thead><tbody>";
      json.forEach(row => {
        html += "<tr>";
        Object.values(row).forEach(val => { html += `<td>${val}</td>`; });
        html += "</tr>";
      });
      html += "</tbody></table>";
      element.innerHTML = html;
      console.log(`Successfully loaded ${sheetName} with ${json.length} rows`);
    })
    .catch(e => { 
      console.error("Error loading data:", e);
      element.innerHTML = `<p>Error loading data: ${e.message}</p>`;
    });
}

// Render summary cards
function renderSummaryCards(model) {
  if (!modelFiles[model]) {
    document.getElementById('summary-cards').innerHTML = "";
    return;
  }
  fetch(modelFiles[model])
    .then(res => res.arrayBuffer())
    .then(data => {
      const workbook = XLSX.read(data);
      const sheet = workbook.Sheets["Summary Statistics"];
      if (!sheet) return;
      const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });
      if (!json.length) return;
      let html = "";
      json.forEach(row => {
        html += `
          <div class="summary-card">
            <h2>${row["Metric"]}</h2>
            <div class="score">${Number(row["Average Score"]).toFixed(2)}</div>
          </div>
        `;
      });
      document.getElementById('summary-cards').innerHTML = html;
    })
    .catch(e => { console.error("Error loading summary cards:", e); });
}

// SIMPLIFIED: Tab switching using only style.display
function switchTab(sub) {
  console.log("Switching to tab:", sub);
  
  // Clear all active sub-tab classes
  document.querySelectorAll('.sub-tab').forEach(btn => btn.classList.remove('active'));
  
  // Set active sub-tab
  const activeSubTab = document.querySelector(`.sub-tab[data-sub="${sub}"]`);
  if (activeSubTab) {
    activeSubTab.classList.add('active');
  }
  
  const model = document.querySelector('.nav-tab.active').getAttribute('data-model');
  console.log("Model:", model);
  
  // Hide all content first
  document.getElementById('current-tab-content').style.display = 'none';
  document.getElementById('category-tab-content').style.display = 'none';
  document.getElementById('summary-cards').style.display = 'none';
  
  // Show content based on selected tab
  if (sub === 'current') {
    document.getElementById('current-tab-content').style.display = 'block';
    document.getElementById('summary-cards').style.display = 'flex';
    renderSummaryCards(model);
    renderTable(model, "Detailed Evaluation", "current-table");
  } else if (sub === 'category') {
    document.getElementById('category-tab-content').style.display = 'block';
    renderTable(model, "Category Analysis", "category-table");
  }
  
  console.log("Tab switch complete");
}

// Set tab listeners
function setSubTabListeners() {
  document.querySelectorAll('.sub-tab').forEach(subTab => {
    subTab.addEventListener('click', function() {
      const sub = this.getAttribute('data-sub');
      console.log("Sub-tab clicked:", sub);
      switchTab(sub);
    });
  });
}

// Model tab listeners
function setModelListeners() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', function() {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      
      const activeSubTab = document.querySelector('.sub-tab.active');
      const currentTab = activeSubTab ? activeSubTab.getAttribute('data-sub') : 'current';
      
      console.log("Model tab clicked, current sub-tab:", currentTab);
      switchTab(currentTab);
    });
  });
}

// Render dashboard
function renderDashboard() {
  document.getElementById('result-dashboard').innerHTML = `
    <div class="result-container">
      <nav class="navbar" id="main-navbar"></nav>
      <div class="sub-navbar" id="sub-navbar"></div>
      <div id="summary-cards" class="summary-cards"></div>
      <div id="current-tab-content" style="display: block;">
        <div id="current-table" class="table-container"></div>
      </div>
      <div id="category-tab-content" style="display: none;">
        <div id="category-table" class="table-container"></div>
      </div>
    </div>
  `;
  
  // Generate model tabs
  document.getElementById('main-navbar').innerHTML = modelTabs.map((tab, i) =>
    `<button class="nav-tab${i === 0 ? ' active' : ''}" data-model="${tab.key}">${tab.label}</button>`
  ).join('');
  
  // Generate sub-tabs
  document.getElementById('sub-navbar').innerHTML = subTabs.map(sub =>
    `<button class="sub-tab${sub.key === 'current' ? ' active' : ''}" data-sub="${sub.key}">${sub.label}</button>`
  ).join('');
  
  // Attach listeners
  setModelListeners();
  setSubTabListeners();
  
  // Initial load
  switchTab('current');
}

// Initial load
document.addEventListener('DOMContentLoaded', renderDashboard);
