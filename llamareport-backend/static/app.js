// 增强功能的JavaScript代码

// 全局变量
let uploadProgress = {};
let processingStatus = {};

// 工具函数
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showMessage('success', '已复制到剪贴板');
    }).catch(() => {
        showMessage('error', '复制失败');
    });
}

// 增强的文件上传功能
function enhancedUploadFiles(files) {
    const uploadPromises = Array.from(files).map(file => uploadSingleFile(file));
    Promise.all(uploadPromises).then(() => {
        loadFileList();
        showMessage('success', `成功上传 ${files.length} 个文件`);
    });
}

async function uploadSingleFile(file) {
    const fileId = Date.now() + '_' + file.name;
    uploadProgress[fileId] = 0;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload/file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        uploadProgress[fileId] = 100;
        
        if (!response.ok) {
            throw new Error(result.detail);
        }
        
        return result;
    } catch (error) {
        uploadProgress[fileId] = -1; // 错误状态
        throw error;
    }
}

// 增强的问答功能
async function enhancedAskQuestion() {
    const question = document.getElementById('queryInput').value.trim();
    if (!question) {
        showMessage('error', '请输入问题');
        return;
    }
    
    // 添加到历史记录
    addToQueryHistory(question);
    
    try {
        const resultElement = document.getElementById('queryResult');
        resultElement.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                正在分析您的问题...
            </div>
        `;
        
        const response = await fetch('/query/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayAnswer(result);
        } else {
            resultElement.innerHTML = `<div class="error">❌ ${result.detail}</div>`;
        }
    } catch (error) {
        document.getElementById('queryResult').innerHTML = 
            `<div class="error">❌ 查询失败: ${error.message}</div>`;
    }
}

function displayAnswer(result) {
    const resultElement = document.getElementById('queryResult');
    
    let sourcesHtml = '';
    if (result.sources && result.sources.length > 0) {
        sourcesHtml = `
            <div style="margin-top: 20px;">
                <h4>📚 参考来源</h4>
                ${result.sources.map((source, index) => `
                    <div class="card" style="margin: 10px 0; font-size: 0.9em;">
                        <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 8px;">
                            <span class="badge">来源 ${index + 1}</span>
                            <button class="btn" style="padding: 4px 8px; font-size: 0.8em;" 
                                    onclick="copyToClipboard('${source.text.replace(/'/g, "\\'")}')">
                                复制
                            </button>
                        </div>
                        <div style="color: #666; line-height: 1.5;">
                            ${source.text.length > 200 ? source.text.substring(0, 200) + '...' : source.text}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    resultElement.innerHTML = `
        <div class="fade-in">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 15px;">
                <h3>🤖 AI回答</h3>
                <button class="btn" style="padding: 6px 12px; font-size: 0.9em;" 
                        onclick="copyToClipboard('${result.answer.replace(/'/g, "\\'")}')">
                    复制回答
                </button>
            </div>
            <div class="card" style="background: #f8f9fa; padding: 20px; line-height: 1.6;">
                ${result.answer}
            </div>
            ${sourcesHtml}
        </div>
    `;
}

// 查询历史记录
let queryHistory = JSON.parse(localStorage.getItem('queryHistory') || '[]');

function addToQueryHistory(question) {
    if (!queryHistory.includes(question)) {
        queryHistory.unshift(question);
        if (queryHistory.length > 10) {
            queryHistory = queryHistory.slice(0, 10);
        }
        localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
        updateQueryHistoryDisplay();
    }
}

function updateQueryHistoryDisplay() {
    // 这个函数可以用来显示查询历史
    // 暂时不实现，可以后续添加
}

// 快捷键支持
document.addEventListener('keydown', function(event) {
    // Ctrl+Enter 提交问题
    if (event.ctrlKey && event.key === 'Enter') {
        const queryInput = document.getElementById('queryInput');
        if (document.activeElement === queryInput) {
            enhancedAskQuestion();
        }
    }
    
    // Esc 清空结果
    if (event.key === 'Escape') {
        clearResults();
    }
});

// 自动保存草稿
let draftTimer;
document.getElementById('queryInput')?.addEventListener('input', function() {
    clearTimeout(draftTimer);
    draftTimer = setTimeout(() => {
        localStorage.setItem('queryDraft', this.value);
    }, 1000);
});

// 页面加载时恢复草稿
window.addEventListener('load', function() {
    const draft = localStorage.getItem('queryDraft');
    if (draft) {
        document.getElementById('queryInput').value = draft;
    }
});

// 文件预览功能
function previewFile(filename) {
    // 这里可以添加文件预览功能
    showMessage('info', `预览功能开发中: ${filename}`);
}

// 批量操作
function selectAllFiles() {
    // 批量选择文件功能
    showMessage('info', '批量操作功能开发中');
}

// 导出功能
function exportResults() {
    const results = document.getElementById('queryResult').innerText;
    if (results) {
        const blob = new Blob([results], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `查询结果_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showMessage('success', '结果已导出');
    } else {
        showMessage('error', '没有可导出的结果');
    }
}

// 主题切换
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('darkTheme', isDark);
    showMessage('success', `已切换到${isDark ? '深色' : '浅色'}主题`);
}

// 页面加载时应用保存的主题
window.addEventListener('load', function() {
    const isDark = localStorage.getItem('darkTheme') === 'true';
    if (isDark) {
        document.body.classList.add('dark-theme');
    }
});

// 增强的错误处理
window.addEventListener('error', function(event) {
    console.error('页面错误:', event.error);
    showMessage('error', '页面发生错误，请刷新重试');
});

// 网络状态检测
window.addEventListener('online', function() {
    showMessage('success', '网络连接已恢复');
});

window.addEventListener('offline', function() {
    showMessage('error', '网络连接已断开');
});

// 性能监控
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log('页面加载时间:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
        }, 0);
    });
}
