<template>
    <div class="data-processor">
        <div class="processor-container">
            <div class="processor-header">
                <h2>数据处理与模型生成</h2>
                <p>选择已上传的地层坐标文件，生成钻孔可视化和地质模型</p>
            </div>

            <!-- 文件选择区域 -->
            <div class="file-selection-section">
                <h3>选择地层坐标文件</h3>
                
                <div class="file-list" v-if="files.length > 0">
                    <div 
                        v-for="file in files" 
                        :key="file.filename"
                        class="file-item"
                        :class="{ 'selected': selectedFile && selectedFile.filename === file.filename }"
                        @click="selectFile(file)"
                    >
                        <div class="file-info">
                            <div class="file-name">{{ file.filename }}</div>
                            <div class="file-meta">
                                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                                <span class="file-type">{{ getFileTypeDisplay(file.file_type) }}</span>
                                <span class="upload-time">{{ formatDateTime(file.upload_time) }}</span>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button 
                                class="btn btn-small btn-primary" 
                                @click.stop="loadFileData(file)"
                                :disabled="loading"
                            >
                                {{ loading && loadingFile === file.filename ? '加载中...' : '加载数据' }}
                            </button>
                        </div>
                    </div>
                </div>

                <div v-else-if="!filesLoading" class="no-files">
                    <p>暂无已上传的地层坐标文件</p>
                    <router-link to="/upload" class="btn btn-primary">去上传文件</router-link>
                </div>

                <div v-if="filesLoading" class="loading">加载文件列表中...</div>
            </div>

            <!-- 数据预览区域 -->
            <div v-if="currentData" class="data-preview-section">
                <h3>数据预览</h3>
                <div class="data-summary">
                    <div class="summary-item">
                        <label>文件名:</label>
                        <span>{{ currentData.filename }}</span>
                    </div>
                    <div class="summary-item">
                        <label>数据点数:</label>
                        <span>{{ currentData.total_points }} 个</span>
                    </div>
                    <div class="summary-item">
                        <label>地层类型:</label>
                        <span>{{ currentData.strata_types.join(', ') }}</span>
                    </div>
                </div>

                <div class="data-table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>地层名称</th>
                                <th>X坐标</th>
                                <th>Y坐标</th>
                                <th>Z坐标</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(point, index) in displayedData" :key="index">
                                <td>{{ point.stratum_name }}</td>
                                <td>{{ point.x_coord.toFixed(2) }}</td>
                                <td>{{ point.y_coord.toFixed(2) }}</td>
                                <td>{{ point.z_coord.toFixed(2) }}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div v-if="currentData.data.length > 20" class="table-pagination">
                        <p>显示前 20 条数据，共 {{ currentData.total_points }} 条</p>
                    </div>
                </div>
            </div>

            <!-- 可视化区域 -->
            <div v-if="currentData" class="visualization-section">
                <h3>钻孔可视化</h3>
                <div class="visualization-controls">
                    <button 
                        class="btn btn-primary" 
                        @click="generateVisualization"
                        :disabled="visualizing"
                    >
                        {{ visualizing ? '生成中...' : '生成钻孔可视化' }}
                    </button>
                    
                    <div class="view-controls" v-if="visualizationGenerated">
                        <label>查看角度:</label>
                        <button class="btn btn-small" @click="resetView">重置视角</button>
                        <button class="btn btn-small" @click="topView">俯视图</button>
                        <button class="btn btn-small" @click="sideView">侧视图</button>
                    </div>
                </div>

                <div class="three-container" ref="threeContainer">
                    <div v-if="!visualizationGenerated" class="placeholder">
                        点击"生成钻孔可视化"开始生成3D模型
                    </div>
                    <div v-if="visualizationGenerated" class="interaction-hint">
                        拖拽旋转 | 滚轮缩放 | 右键平移
                    </div>
                </div>

                <!-- 地层颜色图例 -->
                <div v-if="visualizationGenerated && stratumColors" class="color-legend">
                    <h4>地层颜色图例</h4>
                    <div class="legend-items">
                        <div 
                            v-for="(color, stratum) in stratumColors" 
                            :key="stratum"
                            class="legend-item"
                        >
                            <div class="color-box" :style="{ backgroundColor: color }"></div>
                            <span>{{ stratum }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 模型生成区域 -->
            <div v-if="currentData" class="model-generation-section">
                <h3>地质模型生成</h3>
                <div class="generation-controls">
                    <button 
                        class="btn btn-success btn-large"
                        @click="generateGeologicalModel"
                        :disabled="modelGenerating"
                    >
                        {{ modelGenerating ? '生成中...' : '生成地质模型' }}
                    </button>
                </div>

                <div v-if="modelResult" class="model-result">
                    <div class="result-message" :class="modelResult.success ? 'success' : 'error'">
                        {{ modelResult.message }}
                    </div>
                </div>
            </div>

            <!-- 底部间距 -->
            <div class="bottom-spacer"></div>
        </div>
    </div>
</template>

<script>
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { getStratumFiles, getStratumData, generateGeologicalModel } from '@/utils/api'

export default {
    name: 'DataProcessor',
    data() {
        return {
            files: [],
            filesLoading: true,
            selectedFile: null,
            currentData: null,
            loading: false,
            loadingFile: null,
            
            // 3D可视化相关
            scene: null,
            camera: null,
            renderer: null,
            controls: null,
            visualizing: false,
            visualizationGenerated: false,
            stratumColors: {},
            
            // 模型生成相关
            modelGenerating: false,
            modelResult: null
        }
    },
    computed: {
        displayedData() {
            if (!this.currentData || !this.currentData.data) return []
            return this.currentData.data.slice(0, 20)
        }
    },
    mounted() {
        this.loadFiles()
    },
    beforeUnmount() {
        this.cleanupThreeJS()
    },
    methods: {
        async loadFiles() {
            try {
                this.filesLoading = true
                const response = await getStratumFiles()
                if (response.success) {
                    this.files = response.files
                }
            } catch (error) {
                console.error('加载文件列表失败:', error)
            } finally {
                this.filesLoading = false
            }
        },

        selectFile(file) {
            this.selectedFile = file
        },

        async loadFileData(file) {
            try {
                this.loading = true
                this.loadingFile = file.filename
                
                const response = await getStratumData(file.filename)
                if (response.success) {
                    this.currentData = response
                    this.selectedFile = file
                    this.cleanupVisualization()
                } else {
                    alert('加载数据失败: ' + response.message)
                }
            } catch (error) {
                console.error('加载数据失败:', error)
                alert('加载数据失败: ' + error.message)
            } finally {
                this.loading = false
                this.loadingFile = null
            }
        },

        // Three.js 相关方法
        generateVisualization() {
            if (!this.currentData) return

            this.visualizing = true
            
            setTimeout(() => {
                this.initThreeJS()
                this.createBoreholeVisualization()
                this.visualizing = false
                this.visualizationGenerated = true
            }, 100)
        },

        initThreeJS() {
            const container = this.$refs.threeContainer
            if (!container) return

            // 清理之前的内容
            container.innerHTML = ''

            // 创建场景
            this.scene = new THREE.Scene()
            this.scene.background = new THREE.Color(0xf0f0f0)

            // 创建相机
            const width = container.clientWidth || 800
            const height = 400
            this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)

            // 创建渲染器
            this.renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                alpha: true
            })
            this.renderer.setSize(width, height)
            // 启用gamma校正，提高颜色表现
            this.renderer.gammaOutput = true
            this.renderer.gammaFactor = 2.2
            // 设置像素比，提高清晰度
            this.renderer.setPixelRatio(window.devicePixelRatio)
            container.appendChild(this.renderer.domElement)

            // 添加强化光源设置
            // 提高环境光强度，使颜色更鲜艳
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.8)
            this.scene.add(ambientLight)

            // 主要方向光
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0)
            directionalLight.position.set(50, 50, 50)
            this.scene.add(directionalLight)

            // 添加补充光源从不同方向照亮对象
            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5)
            directionalLight2.position.set(-50, -50, -50)
            this.scene.add(directionalLight2)

            // 添加点光源增强立体感
            const pointLight = new THREE.PointLight(0xffffff, 0.5)
            pointLight.position.set(0, 100, 0)
            this.scene.add(pointLight)

            // 设置相机位置
            this.camera.position.set(50, 50, 50)
            this.camera.lookAt(0, 0, 0)

            // 添加轨道控制器
            this.controls = new OrbitControls(this.camera, this.renderer.domElement)
            this.controls.enableDamping = true // 启用阻尼效果
            this.controls.dampingFactor = 0.05
            this.controls.screenSpacePanning = false
            this.controls.minDistance = 10
            this.controls.maxDistance = 500
            this.controls.maxPolarAngle = Math.PI / 2
        },

        createBoreholeVisualization() {
            if (!this.currentData || !this.scene) return

            // 生成地层颜色
            this.generateStratumColors()

            // 按地层分组数据
            const stratumGroups = {}
            this.currentData.data.forEach(point => {
                if (!stratumGroups[point.stratum_name]) {
                    stratumGroups[point.stratum_name] = []
                }
                stratumGroups[point.stratum_name].push(point)
            })

            // 为每个地层创建钻孔
            Object.keys(stratumGroups).forEach(stratumName => {
                const points = stratumGroups[stratumName]
                const colorHex = this.stratumColors[stratumName]
                const color = new THREE.Color(colorHex)
                
                console.log(`地层 ${stratumName}: 颜色 ${colorHex}, Three.js颜色:`, color)

                points.forEach(point => {
                    // 创建圆柱体几何体
                    const geometry = new THREE.CylinderGeometry(0.5, 0.5, 5, 8)
                    // 使用MeshLambertMaterial，颜色更鲜艳，对光照响应更好
                    const material = new THREE.MeshLambertMaterial({ 
                        color: color,
                        transparent: false,
                        opacity: 1.0
                    })
                    const cylinder = new THREE.Mesh(geometry, material)

                    // 设置位置（注意Three.js的坐标系）
                    cylinder.position.set(
                        point.x_coord / 100, // 缩放坐标以适应显示
                        point.z_coord / 100,
                        point.y_coord / 100
                    )

                    this.scene.add(cylinder)
                })
            })

            // 开始渲染循环
            this.animate()
        },

        generateStratumColors() {
            const strataTypes = this.currentData.strata_types
            // 使用更鲜艳、对比度更高的颜色
            const colors = [
                '#FF0000', // 鲜红色
                '#00FF00', // 鲜绿色
                '#0000FF', // 鲜蓝色
                '#FFFF00', // 鲜黄色
                '#FF00FF', // 品红色
                '#00FFFF', // 青色
                '#FF8000', // 橙色
                '#8000FF', // 紫色
                '#FF0080', // 玫红色
                '#80FF00', // 黄绿色
                '#0080FF', // 天蓝色
                '#FF8080'  // 浅红色
            ]

            this.stratumColors = {}
            strataTypes.forEach((stratum, index) => {
                this.stratumColors[stratum] = colors[index % colors.length]
            })

            console.log('生成的地层颜色映射:', this.stratumColors)
        },

        animate() {
            if (!this.renderer || !this.scene || !this.camera) return

            requestAnimationFrame(() => this.animate())

            // 更新轨道控制器
            if (this.controls) {
                this.controls.update()
            }

            this.renderer.render(this.scene, this.camera)
        },

        resetView() {
            if (this.camera && this.controls) {
                this.camera.position.set(50, 50, 50)
                this.controls.target.set(0, 0, 0)
                this.controls.update()
            }
        },

        topView() {
            if (this.camera && this.controls) {
                this.camera.position.set(0, 100, 0)
                this.controls.target.set(0, 0, 0)
                this.controls.update()
            }
        },

        sideView() {
            if (this.camera && this.controls) {
                this.camera.position.set(100, 0, 0)
                this.controls.target.set(0, 0, 0)
                this.controls.update()
            }
        },

        cleanupVisualization() {
            this.visualizationGenerated = false
            this.stratumColors = {}
            this.cleanupThreeJS()
        },

        cleanupThreeJS() {
            if (this.controls) {
                this.controls.dispose()
                this.controls = null
            }
            if (this.renderer) {
                this.renderer.dispose()
                this.renderer = null
            }
            this.scene = null
            this.camera = null
        },

        // 模型生成
        async generateGeologicalModel() {
            if (!this.currentData) return

            try {
                this.modelGenerating = true
                this.modelResult = null

                const response = await generateGeologicalModel({
                    filename: this.currentData.filename
                })

                this.modelResult = response
            } catch (error) {
                console.error('生成地质模型失败:', error)
                this.modelResult = {
                    success: false,
                    message: '生成地质模型失败: ' + error.message
                }
            } finally {
                this.modelGenerating = false
            }
        },

        // 工具方法
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes'
            const k = 1024
            const sizes = ['Bytes', 'KB', 'MB', 'GB']
            const i = Math.floor(Math.log(bytes) / Math.log(k))
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
        },

        getFileTypeDisplay(fileType) {
            const ext = fileType.replace('.', '').toLowerCase()
            const types = {
                'txt': '地层坐标文件',
                'xlsx': 'Excel 工作簿',
                'xls': 'Excel 文件',
                'csv': 'CSV 文件'
            }
            return types[ext] || fileType.toUpperCase()
        },

        formatDateTime(isoString) {
            if (!isoString) return '-'
            try {
                const date = new Date(isoString)
                return date.toLocaleString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                })
            } catch (e) {
                return isoString
            }
        }
    }
}
</script>

<style scoped>
.data-processor {
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
}

.processor-container {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.processor-header {
    padding: 30px 30px 20px;
    border-bottom: 1px solid #eee;
    text-align: center;
}

.processor-header h2 {
    margin: 0 0 10px 0;
    color: #333;
    font-size: 24px;
}

.processor-header p {
    margin: 0;
    color: #666;
}

/* 文件选择区域 */
.file-selection-section {
    padding: 30px;
    border-bottom: 1px solid #eee;
}

.file-selection-section h3 {
    margin: 0 0 20px 0;
    color: #333;
}

.file-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.file-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s;
}

.file-item:hover {
    border-color: #007bff;
    background-color: #f8f9fa;
}

.file-item.selected {
    border-color: #007bff;
    background-color: #e3f2fd;
}

.file-info {
    flex: 1;
}

.file-name {
    font-weight: 600;
    color: #333;
    margin-bottom: 5px;
}

.file-meta {
    display: flex;
    gap: 15px;
    font-size: 12px;
    color: #666;
}

.file-actions {
    margin-left: 15px;
}

.no-files {
    text-align: center;
    padding: 60px 20px;
    color: #666;
}

.loading {
    text-align: center;
    padding: 40px;
    color: #666;
}

/* 数据预览区域 */
.data-preview-section {
    padding: 30px;
    border-bottom: 1px solid #eee;
}

.data-preview-section h3 {
    margin: 0 0 20px 0;
    color: #333;
}

.data-summary {
    display: flex;
    gap: 30px;
    margin-bottom: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
}

.summary-item {
    display: flex;
    gap: 8px;
}

.summary-item label {
    font-weight: 600;
    color: #555;
}

.summary-item span {
    color: #333;
}

.data-table-container {
    border: 1px solid #ddd;
    border-radius: 6px;
    overflow: hidden;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    background: #f5f5f5;
    padding: 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid #ddd;
}

.data-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #eee;
}

.data-table tr:hover {
    background: #f8f9fa;
}

.table-pagination {
    padding: 10px 15px;
    background: #f8f9fa;
    text-align: center;
    font-size: 14px;
    color: #666;
}

/* 可视化区域 */
.visualization-section {
    padding: 30px;
    border-bottom: 1px solid #eee;
}

.visualization-section h3 {
    margin: 0 0 20px 0;
    color: #333;
}

.visualization-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.view-controls {
    display: flex;
    gap: 10px;
    align-items: center;
}

.view-controls label {
    font-weight: 600;
    color: #555;
}

.three-container {
    width: 100%;
    height: 400px;
    border: 1px solid #ddd;
    border-radius: 6px;
    position: relative;
    overflow: hidden;
}

.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #666;
    font-size: 16px;
}

.interaction-hint {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 10;
}

.color-legend {
    margin-top: 20px;
}

.color-legend h4 {
    margin: 0 0 15px 0;
    color: #333;
}

.legend-items {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.color-box {
    width: 20px;
    height: 20px;
    border-radius: 3px;
    border: 1px solid #ddd;
}

/* 模型生成区域 */
.model-generation-section {
    padding: 30px;
}

.model-generation-section h3 {
    margin: 0 0 20px 0;
    color: #333;
}

.generation-controls {
    text-align: center;
    margin-bottom: 20px;
}

.model-result {
    margin-top: 20px;
}

.result-message {
    padding: 15px;
    border-radius: 6px;
    text-align: center;
}

.result-message.success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.result-message.error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

/* 按钮样式 */
.btn {
    padding: 8px 16px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
    text-decoration: none;
    display: inline-block;
}

.btn-small {
    padding: 6px 12px;
    font-size: 12px;
}

.btn-large {
    padding: 12px 24px;
    font-size: 16px;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #0056b3;
}

.btn-success {
    background: #28a745;
    color: white;
}

.btn-success:hover:not(:disabled) {
    background: #1e7e34;
}

.btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

/* 底部间距 */
.bottom-spacer {
    height: 60px;
}
</style>