<template>
    <div class="upload-page">
        <div class="upload-container">
            <div class="upload-header">
                <h2>地层坐标数据上传</h2>
                <p>支持文本 (.txt)、Excel (.xlsx) 和 CSV (.csv) 格式的地层坐标数据文件</p>
            </div>

            <!-- 文件上传区域 -->
            <div class="upload-section">
                <div class="upload-zone" 
                     :class="{ 'dragover': isDragOver, 'has-file': selectedFile }"
                     @dragenter.prevent="handleDragEnter"
                     @dragover.prevent="handleDragOver"
                     @dragleave.prevent="handleDragLeave"
                     @drop.prevent="handleDrop">
                    
                    <div v-if="!selectedFile" class="upload-placeholder">
                        <i class="upload-icon">📁</i>
                        <p class="upload-text">拖拽文件到此处或点击上传</p>
                        <p class="upload-hint">支持 .txt, .xlsx, .csv 格式，最大 50MB</p>
                        <input type="file" 
                               ref="fileInput" 
                               @change="handleFileSelect" 
                               accept=".txt,.xlsx,.xls,.csv"
                               class="file-input">
                        <button class="upload-btn" @click="$refs.fileInput.click()">
                            选择文件
                        </button>
                    </div>

                    <div v-else class="file-info">
                        <div class="file-details">
                            <i class="file-icon">📊</i>
                            <div class="file-meta">
                                <h3>{{ selectedFile.name }}</h3>
                                <p>大小: {{ formatFileSize(selectedFile.size) }}</p>
                                <p>类型: {{ getFileType(selectedFile.name) }}</p>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button class="btn btn-primary" @click="uploadFile" :disabled="uploading">
                                <span v-if="uploading">上传中...</span>
                                <span v-else>上传文件</span>
                            </button>
                            <button class="btn btn-secondary" @click="removeFile">
                                移除文件
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 上传进度 -->
                <div v-if="uploading" class="upload-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                    </div>
                    <p>上传进度: {{ uploadProgress }}%</p>
                </div>

                <!-- 上传状态消息 -->
                <div v-if="uploadMessage" class="upload-message" :class="uploadStatus">
                    <p>{{ uploadMessage }}</p>
                    <button v-if="uploadStatus === 'success'" class="btn btn-link" @click="viewData">
                        查看数据
                    </button>
                </div>
            </div>

            <!-- 数据预览区域 -->
            <div v-if="previewData" class="preview-section">
                <div class="preview-header">
                    <h3>数据预览</h3>
                    <div class="preview-meta">
                        <span class="data-count">显示前 {{ Math.min(previewData.length, 100) }} 行数据</span>
                        <span class="format-badge stratum">地层坐标格式</span>
                    </div>
                    
                    <!-- 地层坐标统计信息 -->
                    <div v-if="Object.keys(formatStats).length > 0" class="format-stats">
                        <div class="stratum-stats">
                            <p><strong>地层类型：</strong>{{ formatStats.stratum_types }} 种</p>
                            <p><strong>坐标范围：</strong>
                                X: {{ formatStats.coordinate_ranges?.x_min?.toFixed(2) }} ~ {{ formatStats.coordinate_ranges?.x_max?.toFixed(2) }},
                                Y: {{ formatStats.coordinate_ranges?.y_min?.toFixed(2) }} ~ {{ formatStats.coordinate_ranges?.y_max?.toFixed(2) }},
                                Z: {{ formatStats.coordinate_ranges?.z_min?.toFixed(2) }} ~ {{ formatStats.coordinate_ranges?.z_max?.toFixed(2) }}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th v-for="column in previewColumns" :key="column">
                                    {{ column }}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(row, index) in previewData.slice(0, 100)" :key="index">
                                <td v-for="column in previewColumns" :key="column">
                                    {{ row[column] || '-' }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="preview-footer">
                    <p>共 {{ previewData.length }} 行数据</p>
                    <div class="preview-actions">
                        <button class="btn btn-primary" @click="processData">
                            处理数据
                        </button>
                        <button class="btn btn-secondary" @click="showSampleMenu">
                            下载模板
                        </button>
                    </div>
                </div>
            </div>

            <!-- 数据格式说明 -->
            <div class="format-guide">
                <h3>地层坐标数据格式要求</h3>
                
                <div class="guide-content">
                    <div class="guide-item full-width">
                        <h4>地层坐标格式</h4>
                        <p>每行包含四个字段，以空格或制表符分隔：</p>
                        <ul>
                            <li><strong>地层名称</strong>: 地层类型名称（可重复）</li>
                            <li><strong>X坐标</strong>: 地层点的X坐标</li>
                            <li><strong>Y坐标</strong>: 地层点的Y坐标</li>
                            <li><strong>Z坐标</strong>: 地层点的Z坐标（高程）</li>
                        </ul>
                        
                        <div class="format-example">
                            <h5>示例格式：</h5>
                            <pre class="example-code">含砾砂岩层 3029.43 -2982.37 -146.84
含砾砂岩层 3035.35 -2016.46 -152.67
地表层 1042.9 2968 26.21
地表层 2077.9 -3037.73 -3.04</pre>
                        </div>
                        
                        <div class="format-note">
                            <p><strong>注意事项：</strong></p>
                            <ul>
                                <li>地层名称可以重复，表示同一地层的不同位置点</li>
                                <li>坐标数值支持小数</li>
                                <li>TXT文件：字段之间用空格或制表符分隔</li>
                                <li>Excel/CSV文件：数据按列排列（地层名称,X坐标,Y坐标,Z坐标）</li>
                                <li>支持 .txt, .xlsx, .xls, .csv 格式文件</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { uploadStratumData } from '@/utils/api'

export default {
    name: 'BoreholeUpload',
    data() {
        return {
            selectedFile: null,
            isDragOver: false,
            uploading: false,
            uploadProgress: 0,
            uploadMessage: '',
            uploadStatus: '', // success, error, warning
            previewData: null,
            previewColumns: [],
            dataFormat: null, // 上传数据的实际格式
            formatStats: {} // 格式统计信息
        }
    },
    methods: {
        handleDragEnter() {
            this.isDragOver = true
        },

        handleDragOver() {
            this.isDragOver = true
        },

        handleDragLeave() {
            this.isDragOver = false
        },

        handleDrop(e) {
            this.isDragOver = false
            const files = e.dataTransfer.files
            if (files.length > 0) {
                this.selectFile(files[0])
            }
        },

        handleFileSelect(e) {
            const file = e.target.files[0]
            if (file) {
                this.selectFile(file)
            }
        },

        selectFile(file) {
            // 验证文件类型
            const allowedTypes = ['.txt', '.xlsx', '.xls', '.csv']
            const fileExt = '.' + file.name.split('.').pop().toLowerCase()
            
            if (!allowedTypes.includes(fileExt)) {
                this.showMessage('请选择 TXT、Excel 或 CSV 格式的文件', 'error')
                return
            }

            // 验证文件大小 (50MB)
            const maxSize = 50 * 1024 * 1024
            if (file.size > maxSize) {
                this.showMessage('文件大小不能超过 50MB', 'error')
                return
            }

            this.selectedFile = file
            this.clearMessages()
            
            // 重置文件输入框
            this.$refs.fileInput.value = ''
        },

        removeFile() {
            this.selectedFile = null
            this.previewData = null
            this.previewColumns = []
            this.dataFormat = null
            this.formatStats = {}
            this.clearMessages()
        },

        async uploadFile() {
            if (!this.selectedFile) return

            this.uploading = true
            this.uploadProgress = 0
            this.clearMessages()

            try {
                const formData = new FormData()
                formData.append('file', this.selectedFile)

                // 模拟上传进度
                const progressInterval = setInterval(() => {
                    if (this.uploadProgress < 90) {
                        this.uploadProgress += 10
                    }
                }, 200)

                const response = await uploadStratumData(formData, (progress) => {
                    this.uploadProgress = progress
                })

                clearInterval(progressInterval)
                this.uploadProgress = 100

                if (response.success) {
                    this.showMessage(response.message || '文件上传成功！', 'success')
                    
                    // 获取数据预览
                    if (response.preview_data) {
                        this.previewData = response.preview_data
                        this.previewColumns = response.columns || []
                        this.dataFormat = response.data_format || 'standard'
                        this.formatStats = response.format_stats || {}
                    }
                } else {
                    this.showMessage(response.message || '上传失败', 'error')
                }

            } catch (error) {
                this.showMessage('上传失败: ' + (error.message || '网络错误'), 'error')
            } finally {
                this.uploading = false
                setTimeout(() => {
                    this.uploadProgress = 0
                }, 2000)
            }
        },



        processData() {
            // 触发数据处理流程
            this.$emit('data-ready', {
                file: this.selectedFile,
                data: this.previewData,
                columns: this.previewColumns
            })
            
            this.showMessage('数据已准备好进行处理', 'success')
        },

        downloadSample(format = 'txt') {
            const sampleData = [
                ['含砾砂岩层', 3029.43, -2982.37, -146.84],
                ['含砾砂岩层', 3035.35, -2016.46, -152.67],
                ['含砾砂岩层', 2987.21, -3001.15, -149.35],
                ['地表层', 1042.9, 2968, 26.21],
                ['地表层', 2077.9, -3037.73, -3.04],
                ['地表层', 1156.32, 2845.67, 28.45],
                ['砂质泥岩层', 2654.18, -1879.42, -178.92],
                ['砂质泥岩层', 3201.67, -2345.78, -185.33],
                ['砂质泥岩层', 2876.54, -2123.98, -181.67]
            ]

            let content, filename, mimeType

            if (format === 'csv') {
                // CSV格式
                content = sampleData.map(row => row.join(',')).join('\n')
                filename = '地层坐标数据模板.csv'
                mimeType = 'text/csv;charset=utf-8;'
            } else {
                // TXT格式（默认）
                content = sampleData.map(row => row.join(' ')).join('\n')
                filename = '地层坐标数据模板.txt'
                mimeType = 'text/plain;charset=utf-8;'
            }

            // 下载文件
            const blob = new Blob([content], { type: mimeType })
            const link = document.createElement('a')
            const url = URL.createObjectURL(blob)
            link.setAttribute('href', url)
            link.setAttribute('download', filename)
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        },

        showSampleMenu() {

            // 简单的选择菜单
            const choice = window.confirm('选择下载格式：\n确定 = TXT格式\n取消 = CSV格式')
            if (choice) {
                this.downloadSample('txt')
            } else {
                this.downloadSample('csv')
            }
        },

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes'
            const k = 1024
            const sizes = ['Bytes', 'KB', 'MB', 'GB']
            const i = Math.floor(Math.log(bytes) / Math.log(k))
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
        },

        getFileType(filename) {
            const ext = filename.split('.').pop().toLowerCase()
            const types = {
                'txt': '地层坐标文件',
                'xlsx': 'Excel 工作簿',
                'xls': 'Excel 97-2003',
                'csv': 'CSV 文件'
            }
            return types[ext] || '未知格式'
        },

        showMessage(message, status) {
            this.uploadMessage = message
            this.uploadStatus = status
            
            if (status === 'success') {
                setTimeout(() => {
                    this.clearMessages()
                }, 5000)
            }
        },

        clearMessages() {
            this.uploadMessage = ''
            this.uploadStatus = ''
        }
    }
}
</script>

<style scoped>
.upload-page {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.upload-container {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.upload-header {
    padding: 30px 30px 20px;
    border-bottom: 1px solid #eee;
    text-align: center;
}

.upload-header h2 {
    margin: 0 0 10px 0;
    color: #333;
    font-size: 24px;
}

.upload-header p {
    margin: 0;
    color: #666;
}

.upload-section {
    padding: 30px;
}

.upload-zone {
    border: 2px dashed #ddd;
    border-radius: 8px;
    padding: 40px 20px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
}

.upload-zone.dragover {
    border-color: #007bff;
    background-color: #f8f9fa;
}

.upload-zone.has-file {
    border-color: #28a745;
    cursor: default;
}

.upload-placeholder .upload-icon {
    font-size: 48px;
    display: block;
    margin-bottom: 20px;
}

.upload-text {
    font-size: 18px;
    color: #333;
    margin: 0 0 10px 0;
}

.upload-hint {
    color: #666;
    margin: 0 0 20px 0;
}

.file-input {
    display: none;
}

.upload-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s;
}

.upload-btn:hover {
    background: #0056b3;
}

.file-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.file-details {
    display: flex;
    align-items: center;
    gap: 15px;
}

.file-icon {
    font-size: 32px;
}

.file-meta h3 {
    margin: 0 0 5px 0;
    color: #333;
}

.file-meta p {
    margin: 0;
    color: #666;
    font-size: 14px;
}

.file-actions {
    display: flex;
    gap: 10px;
}

.btn {
    padding: 8px 16px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #0056b3;
}

.btn-primary:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background: #545b62;
}

.btn-link {
    background: none;
    color: #007bff;
    text-decoration: underline;
}

.upload-progress {
    margin-top: 20px;
    text-align: center;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #eee;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background: #007bff;
    transition: width 0.3s ease;
}

.upload-message {
    margin-top: 20px;
    padding: 15px;
    border-radius: 4px;
    text-align: center;
}

.upload-message.success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.upload-message.error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

.upload-message.warning {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
}

.preview-section {
    margin-top: 30px;
    padding: 30px;
    border-top: 1px solid #eee;
}

.preview-header {
    margin-bottom: 20px;
}

.preview-header h3 {
    margin: 0 0 5px 0;
    color: #333;
}

.preview-header p {
    margin: 0;
    color: #666;
}

.preview-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.data-count {
    color: #666;
    font-size: 14px;
}

.format-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.format-badge.stratum {
    background-color: #f3e5f5;
    color: #7b1fa2;
}

.format-stats {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 15px;
}

.format-stats p {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #495057;
}

.format-stats p:last-child {
    margin-bottom: 0;
}

.stratum-stats strong {
    color: #212529;
}

.table-container {
    max-height: 400px;
    overflow: auto;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.data-table th,
.data-table td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #eee;
}

.data-table th {
    background: #f8f9fa;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
}

.data-table tr:hover {
    background: #f8f9fa;
}

.preview-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #eee;
}

.preview-actions {
    display: flex;
    gap: 10px;
}

.format-guide {
    padding: 30px;
    border-top: 1px solid #eee;
    background: #f8f9fa;
}

.format-guide h3 {
    margin: 0 0 20px 0;
    color: #333;
}



.guide-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
}

.guide-item h4 {
    margin: 0 0 15px 0;
    color: #007bff;
    font-size: 16px;
}

.guide-item ul {
    margin: 0;
    padding-left: 20px;
}

.guide-item li {
    margin-bottom: 8px;
    line-height: 1.5;
}

.guide-item.full-width {
    grid-column: 1 / -1;
}

.format-example {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 15px;
    margin: 15px 0;
}

.format-example h5 {
    margin: 0 0 10px 0;
    color: #495057;
    font-size: 14px;
}

.example-code {
    background: #2d3748;
    color: #e2e8f0;
    padding: 12px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.4;
    margin: 0;
    overflow-x: auto;
}

.format-note {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 4px;
    padding: 15px;
    margin-top: 15px;
}

.format-note p {
    margin: 0 0 10px 0;
    font-weight: 600;
    color: #856404;
}

.format-note ul {
    margin: 0;
    padding-left: 20px;
}

.format-note li {
    color: #856404;
    margin-bottom: 5px;
}

@media (max-width: 768px) {
    .upload-page {
        padding: 15px;
    }

    .upload-container {
        margin: 0;
    }

    .upload-header,
    .upload-section,
    .preview-section,
    .format-guide {
        padding: 20px 15px;
    }

    .file-info {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
    }

    .guide-content {
        grid-template-columns: 1fr;
        gap: 20px;
    }

    .preview-footer {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
    }

    .table-container {
        max-height: 300px;
    }
}
</style>