# 前端集成 Agent 系统指南

## 📋 概述

本指南说明如何在前端集成新的 Agent 系统,实现智能年报分析功能。

---

## 🔄 两个系统的区别

### 1. 原有的简单查询系统
- **接口**: `POST /query/ask`
- **功能**: 简单的 RAG 问答
- **输出**: 纯文本答案
- **适用场景**: 快速查询单个问题

### 2. 新的 Agent 系统
- **接口**: `POST /agent/generate-report` 或 `POST /agent/query`
- **功能**: 智能分析,结构化输出
- **输出**: Markdown 格式的专业分析报告
- **适用场景**: 深度分析,生成完整报告

---

## 🎯 前端集成方案

### 方案 1: 添加"生成报告"按钮

在现有的查询界面添加一个新按钮,用于生成完整的年报分析报告。

#### 前端代码示例 (React/Vue)

```javascript
// API 调用函数
async function generateReport(companyName, year) {
  const response = await fetch('http://localhost:8000/agent/generate-report', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      company_name: companyName,
      year: year,
      save_to_file: true
    })
  });
  
  const result = await response.json();
  return result;
}

// 使用示例
const result = await generateReport('新乡天力锂能股份有限公司', '2023');
console.log(result.report); // Markdown 格式的报告
```

#### UI 设计建议

```html
<!-- 在现有的查询界面添加 -->
<div class="query-actions">
  <button class="btn-query" onclick="handleQuery()">
    🔍 提问
  </button>
  
  <button class="btn-generate-report" onclick="handleGenerateReport()">
    📊 获取建议
  </button>
  
  <button class="btn-clear" onclick="handleClear()">
    🗑️ 清空结果
  </button>
</div>
```

---

### 方案 2: 智能查询增强

保留原有的查询按钮,但在后台使用 Agent 系统来增强回答质量。

#### 前端代码示例

```javascript
// 智能查询函数
async function smartQuery(question) {
  const response = await fetch('http://localhost:8000/agent/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: question
    })
  });
  
  const result = await response.json();
  return result;
}

// 使用示例
const result = await smartQuery('公司的主要业务是什么?');
console.log(result.answer); // 结构化的 Markdown 答案
```

---

### 方案 3: 分步骤生成报告

提供更细粒度的控制,让用户选择生成哪些章节。

#### 前端代码示例

```javascript
// 生成单个章节
async function generateSection(sectionName, companyName, year) {
  const response = await fetch('http://localhost:8000/agent/generate-section', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      section_name: sectionName,
      company_name: companyName,
      year: year
    })
  });
  
  const result = await response.json();
  return result;
}

// 使用示例
const sections = [
  'financial_review',      // 财务点评
  'business_guidance',     // 业绩指引
  'business_highlights',   // 业务亮点
  'profit_forecast'        // 盈利预测
];

for (const section of sections) {
  const result = await generateSection(section, '新乡天力锂能股份有限公司', '2023');
  console.log(result.content);
}
```

---

## 📊 API 端点详解

### 1. 生成完整报告

```http
POST /agent/generate-report
Content-Type: application/json

{
  "company_name": "新乡天力锂能股份有限公司",
  "year": "2023",
  "save_to_file": true,
  "output_path": "reports/report.md"
}
```

**响应**:
```json
{
  "status": "success",
  "report": "# 新乡天力锂能股份有限公司 2023年年报业绩点评\n\n...",
  "saved_to": "reports/新乡天力_2023_完整报告.md",
  "generation_time": 120.5
}
```

---

### 2. 智能查询

```http
POST /agent/query
Content-Type: application/json

{
  "question": "公司的主要业务是什么?"
}
```

**响应**:
```json
{
  "status": "success",
  "answer": "## 新乡天力锂能股份有限公司2023年主要业务概况\n\n...",
  "query_time": 5.2
}
```

---

### 3. 生成单个章节

```http
POST /agent/generate-section
Content-Type: application/json

{
  "section_name": "financial_review",
  "company_name": "新乡天力锂能股份有限公司",
  "year": "2023"
}
```

**响应**:
```json
{
  "status": "success",
  "section": "financial_review",
  "content": "## 一、财务点评\n\n...",
  "generation_time": 30.2
}
```

---

### 4. 检查 Agent 状态

```http
GET /agent/status
```

**响应**:
```json
{
  "rag_engine_initialized": true,
  "report_agent_initialized": true,
  "template_renderer_initialized": false,
  "index_loaded": true,
  "ready": true,
  "message": "Agent 系统已就绪"
}
```

---

## 🎨 UI/UX 建议

### 1. 加载状态

生成报告可能需要 2-5 分钟,需要良好的加载提示:

```javascript
// 显示进度
function showProgress(message) {
  const progressDiv = document.getElementById('progress');
  progressDiv.innerHTML = `
    <div class="loading-spinner"></div>
    <p>${message}</p>
    <p class="hint">这可能需要 2-5 分钟,请耐心等待...</p>
  `;
}

// 使用
showProgress('正在生成财务点评章节...');
```

---

### 2. Markdown 渲染

Agent 返回的是 Markdown 格式,需要渲染成 HTML:

```javascript
// 使用 marked.js 渲染 Markdown
import { marked } from 'marked';

function renderMarkdown(markdown) {
  const html = marked.parse(markdown);
  document.getElementById('result').innerHTML = html;
}
```

---

### 3. 下载报告

提供下载功能:

```javascript
function downloadReport(content, filename) {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// 使用
downloadReport(result.report, '新乡天力_2023_年报分析.md');
```

---

## 🔧 完整示例

### HTML

```html
<!DOCTYPE html>
<html>
<head>
  <title>智能年报分析</title>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
  <div class="container">
    <h1>🤖 智能问答</h1>
    
    <textarea id="question" placeholder="请输入您的问题..."></textarea>
    
    <div class="actions">
      <button onclick="handleQuery()">🔍 提问</button>
      <button onclick="handleGenerateReport()">📊 获取建议</button>
      <button onclick="handleClear()">🗑️ 清空结果</button>
    </div>
    
    <div id="progress" style="display: none;"></div>
    <div id="result"></div>
  </div>
  
  <script src="app.js"></script>
</body>
</html>
```

### JavaScript (app.js)

```javascript
const API_BASE = 'http://localhost:8000';

// 智能查询
async function handleQuery() {
  const question = document.getElementById('question').value;
  if (!question) return;
  
  showProgress('正在分析您的问题...');
  
  try {
    const response = await fetch(`${API_BASE}/agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    
    const result = await response.json();
    hideProgress();
    
    if (result.status === 'success') {
      renderMarkdown(result.answer);
    } else {
      showError(result.error);
    }
  } catch (error) {
    hideProgress();
    showError(error.message);
  }
}

// 生成完整报告
async function handleGenerateReport() {
  showProgress('正在生成完整年报分析...<br>这可能需要 2-5 分钟,请耐心等待...');
  
  try {
    const response = await fetch(`${API_BASE}/agent/generate-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_name: '新乡天力锂能股份有限公司',
        year: '2023',
        save_to_file: true
      })
    });
    
    const result = await response.json();
    hideProgress();
    
    if (result.status === 'success') {
      renderMarkdown(result.report);
      
      // 提供下载按钮
      showDownloadButton(result.report, '年报分析.md');
    } else {
      showError(result.error);
    }
  } catch (error) {
    hideProgress();
    showError(error.message);
  }
}

// 渲染 Markdown
function renderMarkdown(markdown) {
  const html = marked.parse(markdown);
  document.getElementById('result').innerHTML = html;
}

// 显示/隐藏进度
function showProgress(message) {
  const progressDiv = document.getElementById('progress');
  progressDiv.innerHTML = `
    <div class="loading-spinner"></div>
    <p>${message}</p>
  `;
  progressDiv.style.display = 'block';
}

function hideProgress() {
  document.getElementById('progress').style.display = 'none';
}

// 清空结果
function handleClear() {
  document.getElementById('result').innerHTML = '';
  document.getElementById('question').value = '';
}
```

---

## 📝 总结

### 推荐方案

1. **短期**: 添加"获取建议"按钮,调用 `/agent/query` 接口
2. **中期**: 添加"生成报告"功能,调用 `/agent/generate-report` 接口
3. **长期**: 实现分步骤生成,提供更细粒度的控制

### 关键点

- ✅ Agent 系统提供更专业、结构化的分析
- ✅ 需要良好的加载状态提示(2-5分钟)
- ✅ 使用 Markdown 渲染库显示结果
- ✅ 提供下载功能方便用户保存报告

---

**开始集成吧!** 🚀

