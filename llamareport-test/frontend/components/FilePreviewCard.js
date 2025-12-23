// 文件预览卡片组件
export default {
    name: 'FilePreviewCard',
    props: {
        files: {
            type: Array,
            default: () => []
        }
    },
    emits: ['file-selected', 'file-uploaded', 'file-deleted'],
    data() {
        return {
            isDragging: false,
            selectedFile: null
        };
    },
    methods: {
        handleDragOver(e) {
            e.preventDefault();
            this.isDragging = true;
        },
        handleDragLeave() {
            this.isDragging = false;
        },
        async handleDrop(e) {
            e.preventDefault();
            this.isDragging = false;
            const files = Array.from(e.dataTransfer.files);
            await this.uploadFiles(files);
        },
        handleFileSelect(e) {
            const files = Array.from(e.target.files);
            this.uploadFiles(files);
        },
        async uploadFiles(files) {
            for (const file of files) {
                if (file.type !== 'application/pdf') {
                    this.$emit('show-message', 'error', `文件 ${file.name} 不是PDF格式`);
                    continue;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload/file', {
                        method: 'POST',
                        body: formData
                    });
                    
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
            }
        },
        selectFile(file) {
            this.selectedFile = file;
            this.$emit('file-selected', file);
        },
        async deleteFile(filename, e) {
            e.stopPropagation();
            if (!confirm(`确定要删除文件 "${filename}" 吗？`)) {
                return;
            }
            
            try {
                const response = await fetch(`/upload/file/${encodeURIComponent(filename)}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    this.$emit('file-deleted');
                    this.$emit('show-message', 'success', `文件 ${filename} 删除成功`);
                    if (this.selectedFile?.filename === filename) {
                        this.selectedFile = null;
                    }
                } else {
                    this.$emit('show-message', 'error', `删除失败: ${result.detail}`);
                }
            } catch (error) {
                this.$emit('show-message', 'error', `删除失败: ${error.message}`);
            }
        },
        formatFileSize(bytes) {
            return (bytes / 1024 / 1024).toFixed(2) + ' MB';
        }
    },
    template: `
        <Card 
            title="文件预览" 
            icon="📁"
            :status="files.length > 0 ? 'content' : 'empty'"
            empty-text="请上传PDF文件"
        >
            <template #default>
                <div 
                    :class="['upload-zone', { dragover: isDragging }]"
                    @dragover.prevent="handleDragOver"
                    @dragleave="handleDragLeave"
                    @drop="handleDrop"
                    @click="$refs.fileInput.click()"
                >
                    <input 
                        ref="fileInput"
                        type="file" 
                        class="file-input" 
                        accept=".pdf" 
                        multiple
                        @change="handleFileSelect"
                    >
                    <p>点击或拖拽上传PDF文件</p>
                </div>
                <div v-if="files.length > 0" class="file-list">
                    <div 
                        v-for="file in files" 
                        :key="file.filename"
                        :class="['file-item', { active: selectedFile?.filename === file.filename }]"
                        @click="selectFile(file)"
                    >
                        <div class="file-info">
                            <span class="file-icon">📄</span>
                            <div class="file-details">
                                <div class="file-name">{{ file.filename }}</div>
                                <div class="file-size">{{ formatFileSize(file.file_size) }}</div>
                            </div>
                        </div>
                        <button 
                            class="file-delete-btn"
                            @click="deleteFile(file.filename, $event)"
                        >
                            ×
                        </button>
                    </div>
                </div>
            </template>
        </Card>
    `
};
