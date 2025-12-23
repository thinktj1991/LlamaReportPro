// 文件预览卡片组件 - 增强版
(function() {
    'use strict';
    
    if (typeof window === 'undefined') return;
    
    // 初始化全局组件对象
    if (!window.Components) {
        window.Components = {};
    }
    
    window.Components.FilePreviewCard = {
        name: 'FilePreviewCard',
        props: { files: { type: Array, default: () => [] } },
        emits: ['file-selected', 'file-uploaded', 'file-deleted', 'show-message', 'file-process'],
        data() {
            return { 
                isDragging: false, 
                selectedFile: null, 
                processingFile: null,
                previewFile: null,
                showPreview: false
            };
        },
        methods: {
            handleDragOver(e) { e.preventDefault(); this.isDragging = true; },
            handleDragLeave() { this.isDragging = false; },
            async handleDrop(e) {
                e.preventDefault();
                this.isDragging = false;
                await this.uploadFiles(Array.from(e.dataTransfer.files));
            },
            handleFileSelect(e) { this.uploadFiles(Array.from(e.target.files)); },
            async uploadFiles(files) {
                // 支持批量上传
                if (files.length > 1) {
                    await this.batchUploadFiles(files);
                } else {
                    for (const file of files) {
                        await this.uploadSingleFile(file);
                    }
                }
            },
            async uploadSingleFile(file) {
                if (file.type !== 'application/pdf') {
                    this.$emit('show-message', 'error', `文件 ${file.name} 不是PDF格式`);
                    return;
                }
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const response = await fetch('/upload/file', { method: 'POST', body: formData });
                    const result = await response.json();
                    if (response.ok) {
                        this.$emit('file-uploaded');
                        this.$emit('show-message', 'success', `文件 ${result.filename} 上传成功`);
                    } else {
                        this.$emit('show-message', 'error', `上传失败: ${result.detail}`);
                    }
                } catch (error) {
                    this.$emit('show-message', 'error', `上传失败: ${error.message}`);
                }
            },
            async batchUploadFiles(files) {
                const formData = new FormData();
                files.forEach(file => {
                    if (file.type === 'application/pdf') {
                        formData.append('files', file);
                    }
                });
                try {
                    const response = await fetch('/upload/files', { method: 'POST', body: formData });
                    const result = await response.json();
                    if (response.ok) {
                        this.$emit('file-uploaded');
                        this.$emit('show-message', 'success', result.message);
                    } else {
                        this.$emit('show-message', 'error', result.detail);
                    }
                } catch (error) {
                    this.$emit('show-message', 'error', `批量上传失败: ${error.message}`);
                }
            },
            selectFile(file) { this.selectedFile = file; this.$emit('file-selected', file); },
            async deleteFile(filename, e) {
                e.stopPropagation();
                if (!confirm(`确定要删除文件 "${filename}" 吗？`)) return;
                try {
                    const response = await fetch(`/upload/file/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                    const result = await response.json();
                    if (response.ok) {
                        this.$emit('file-deleted');
                        this.$emit('show-message', 'success', `文件 ${filename} 删除成功`);
                        if (this.selectedFile?.filename === filename) this.selectedFile = null;
                    } else {
                        this.$emit('show-message', 'error', `删除失败: ${result.detail}`);
                    }
                } catch (error) {
                    this.$emit('show-message', 'error', `删除失败: ${error.message}`);
                }
            },
            async clearAllFiles() {
                if (!confirm('确定要清空所有上传的文件吗？此操作不可恢复！')) return;
                try {
                    const response = await fetch('/upload/clear', { method: 'DELETE' });
                    const result = await response.json();
                    if (response.ok) {
                        this.$emit('file-deleted');
                        this.$emit('show-message', 'success', result.message);
                        this.selectedFile = null;
                    } else {
                        this.$emit('show-message', 'error', result.detail);
                    }
                } catch (error) {
                    this.$emit('show-message', 'error', `清空失败: ${error.message}`);
                }
            },
            async processFile(filename) {
                if (!filename) {
                    this.$emit('show-message', 'error', '请先选择文件');
                    return;
                }
                if (!confirm(`确定要处理文件 "${filename}" 吗？\n\n处理过程包括：\n1. 解析PDF文档\n2. 提取表格数据\n3. 构建RAG索引\n\n这可能需要几分钟时间。`)) {
                    return;
                }
                this.processingFile = filename;
                this.$emit('file-process', filename);
                // 处理完成后重置状态
                setTimeout(() => {
                    this.processingFile = null;
                }, 1000);
            },
            formatFileSize(bytes) { return (bytes / 1024 / 1024).toFixed(2) + ' MB'; },
            openPreview(file) {
                this.previewFile = file;
                this.showPreview = true;
            },
            closePreview() {
                this.showPreview = false;
                this.previewFile = null;
            },
            getPreviewUrl(filename) {
                return `/upload/file/${encodeURIComponent(filename)}`;
            }
        },
        template: `
            <Card title="文件预览" icon="📁" status="content" empty-text="请上传PDF文件">
                <template #default>
                    <div class="file-actions">
                        <button class="btn-small" @click="processFile(selectedFile?.filename)" :disabled="!selectedFile || processingFile || files.length === 0">
                            {{ processingFile ? '处理中...' : '🔄 处理选中文件' }}
                        </button>
                        <button class="btn-small btn-danger" @click="clearAllFiles" :disabled="files.length === 0">🗑️ 清空所有</button>
                    </div>
                    <div :class="['upload-zone', { dragover: isDragging }]" @dragover.prevent="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop" @click="$refs.fileInput.click()">
                        <input ref="fileInput" type="file" class="file-input" accept=".pdf" multiple @change="handleFileSelect">
                        <p>点击或拖拽上传PDF文件</p>
                    </div>
                    <div v-if="files.length > 0" class="file-list">
                        <div v-for="file in files" :key="file.filename" :class="['file-item', { active: selectedFile?.filename === file.filename }]" @click="selectFile(file)">
                            <div class="file-info">
                                <span class="file-icon">📄</span>
                                <div class="file-details">
                                    <div class="file-name">{{ file.filename }}</div>
                                    <div class="file-size">{{ formatFileSize(file.file_size) }}</div>
                                </div>
                            </div>
                            <div class="file-actions-right">
                                <button class="file-preview-btn" @click.stop="openPreview(file)" title="预览文档">📑</button>
                                <button class="file-delete-btn" @click.stop="deleteFile(file.filename, $event)" title="删除文件">×</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- PDF预览模态框 -->
                    <div v-if="showPreview && previewFile" class="pdf-preview-modal" @click.self="closePreview">
                        <div class="pdf-preview-container">
                            <div class="pdf-preview-header">
                                <h3>📄 {{ previewFile.filename }}</h3>
                                <button class="close-preview-btn" @click="closePreview">×</button>
                            </div>
                            <div class="pdf-preview-content">
                                <iframe 
                                    :src="getPreviewUrl(previewFile.filename)" 
                                    class="pdf-preview-iframe"
                                    frameborder="0"
                                ></iframe>
                            </div>
                        </div>
                    </div>
                </template>
            </Card>
        `
    };
    
    console.log('✅ FilePreviewCard组件已加载');
})();
