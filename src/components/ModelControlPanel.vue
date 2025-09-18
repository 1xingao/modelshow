<template>
    <div class="model-control-panel">
        <div class="panel-header">
            <h3>模型控制</h3>
        </div>

        <!-- 模型操作按钮 -->
        <div class="control-section">
            <h4>模型操作</h4>
            <div class="button-group">
                <button @click="loadModel" class="control-btn primary" :disabled="loading">
                    {{ loading ? '加载中...' : '加载模型' }}
                </button>
                <button @click="clearModel" class="control-btn danger" :disabled="!modelLoaded">
                    清除模型
                </button>
                <button @click="resetCamera" class="control-btn" :disabled="!modelLoaded">
                    重新定位
                </button>
                <button @click="findModel" class="control-btn secondary" :disabled="!modelLoaded">
                    查找模型
                </button>
            </div>
        </div>

        <!-- 显示选项 -->
        <div class="control-section">
            <h4>显示选项</h4>
            <div class="checkbox-group">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="showWireframe" @change="toggleWireframe" />
                    显示边缘线
                </label>
                <div v-if="showWireframe" class="edge-color-control">
                    <label class="color-label">边缘线颜色:</label>
                    <input type="color" v-model="edgeColorHex" @change="updateEdgeColor" class="color-picker" />
                </div>
                
                <label class="checkbox-label">
                    <input type="checkbox" v-model="showCoordinateAxis" @change="toggleCoordinateAxis" />
                    显示坐标轴
                </label>
                <div v-if="showCoordinateAxis" class="axis-color-control">
                    <label class="color-label">坐标轴颜色:</label>
                    <input type="color" v-model="axisColorHex" @change="updateAxisColor" class="color-picker" />
                </div>
            </div>
        </div>

        <!-- 视角控制 -->
        <div class="control-section">
            <h4>视角控制</h4>
            <div class="view-buttons">
                <button @click="setView('front')" class="view-btn">前视图</button>
                <button @click="setView('back')" class="view-btn">后视图</button>
                <button @click="setView('left')" class="view-btn">左视图</button>
                <button @click="setView('right')" class="view-btn">右视图</button>
                <button @click="setView('top')" class="view-btn">顶视图</button>
                <button @click="setView('bottom')" class="view-btn">底视图</button>
            </div>
        </div>

        <!-- 地层管理 -->
        <div class="control-section">
            <h4>地层管理</h4>
            <div class="layers-list" v-if="layers.length > 0">
                <div v-for="layer in layers" :key="layer.id" class="layer-item">
                    <label class="layer-label">
                        <input type="checkbox" v-model="layer.visible" @change="toggleLayerVisibility(layer)" />
                        <span class="layer-name">{{ layer.name }}</span>
                    </label>
                    <div class="opacity-control">
                        <label class="opacity-label">透明度:</label>
                        <input type="range" min="0" max="1" step="0.01" v-model="layer.opacity"
                            @input="updateLayerOpacity(layer)" class="opacity-slider" />
                        <span class="opacity-value">{{ Math.round(layer.opacity * 100) }}%</span>
                    </div>
                </div>
            </div>
            <div v-else class="no-layers">
                暂无地层数据
            </div>
        </div>

        <!-- 模型信息 -->
        <div class="control-section" v-if="modelInfo">
            <h4>模型信息</h4>
            <div class="info-item">
                <span class="info-label">文件:</span>
                <span class="info-value">{{ modelInfo.fileName }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">顶点数:</span>
                <span class="info-value">{{ modelInfo.vertices }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">面数:</span>
                <span class="info-value">{{ modelInfo.faces }}</span>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ModelControlPanel',
    props: {
        modelLoaded: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        },
        layers: {
            type: Array,
            default: () => []
        },
        modelInfo: {
            type: Object,
            default: null
        }
    },
    data() {
        return {
            showWireframe: false,
            edgeColorHex: '#000000', // 默认黑色
            showCoordinateAxis: false,
            axisColorHex: '#333333' // 默认深灰色
        }
    },
    methods: {
        /**
         * 加载模型
         */
        loadModel() {
            this.$emit('load-model');
        },

        /**
         * 清除模型
         */
        clearModel() {
            this.$emit('clear-model');
        },

        /**
         * 重置相机位置
         */
        resetCamera() {
            this.$emit('reset-camera');
        },

        /**
         * 查找模型
         */
        findModel() {
            this.$emit('find-model');
        },

        /**
         * 切换边缘线显示
         */
        toggleWireframe() {
            this.$emit('toggle-wireframe', this.showWireframe);
        },

        /**
         * 更新边缘线颜色
         */
        updateEdgeColor() {
            const colorValue = parseInt(this.edgeColorHex.replace('#', ''), 16);
            this.$emit('update-edge-color', colorValue);
        },

        /**
         * 设置视角
         * @param {string} viewType - 视角类型 (front, back, left, right, top, bottom)
         */
        setView(viewType) {
            this.$emit('set-view', viewType);
        },

        /**
         * 切换地层可见性
         * @param {Object} layer - 地层对象
         */
        toggleLayerVisibility(layer) {
            this.$emit('toggle-layer-visibility', {
                layerId: layer.id,
                visible: layer.visible
            });
        },

        /**
         * 更新地层透明度
         * @param {Object} layer - 地层对象
         */
        updateLayerOpacity(layer) {
            this.$emit('update-layer-opacity', {
                layerId: layer.id,
                opacity: parseFloat(layer.opacity)
            });
        },

        /**
         * 切换坐标轴显示
         */
        toggleCoordinateAxis() {
            this.$emit('toggle-coordinate-axis');
        },

        /**
         * 更新坐标轴颜色
         */
        updateAxisColor() {
            const color = parseInt(this.axisColorHex.slice(1), 16);
            this.$emit('update-axis-color', color);
        }
    }
}
</script>

<style scoped>
.model-control-panel {
    width: 300px;
    min-width: 300px;
    max-width: 300px;
    height: 100vh;
    background-color: #f8f9fa;
    border-right: 1px solid #e9ecef;
    padding: 20px;
    overflow-y: auto;
    overflow-x: hidden;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
    box-sizing: border-box;
}

.panel-header {
    margin-bottom: 20px;
    border-bottom: 2px solid #007bff;
    padding-bottom: 10px;
}

.panel-header h3 {
    margin: 0;
    color: #343a40;
    font-weight: 600;
}

.control-section {
    margin-bottom: 25px;
    padding: 15px;
    background-color: white;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
}

.control-section h4 {
    margin: 0 0 15px 0;
    color: #495057;
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.button-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.control-btn {
    padding: 10px 15px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    background-color: #6c757d;
    color: white;
}

.control-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.control-btn.primary {
    background-color: #007bff;
}

.control-btn.primary:hover:not(:disabled) {
    background-color: #0056b3;
}

.control-btn.danger {
    background-color: #dc3545;
}

.control-btn.danger:hover:not(:disabled) {
    background-color: #c82333;
}

.control-btn.secondary {
    background-color: #6f42c1;
}

.control-btn.secondary:hover:not(:disabled) {
    background-color: #5a32a3;
}

.checkbox-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.checkbox-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    font-size: 14px;
}

.checkbox-label input[type="checkbox"] {
    margin-right: 8px;
    transform: scale(1.2);
}

.edge-color-control,
.axis-color-control {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.color-label {
    font-size: 12px;
    color: #6c757d;
    white-space: nowrap;
}

.color-picker {
    width: 40px;
    height: 30px;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
}

.view-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.view-btn {
    padding: 8px 12px;
    border: 1px solid #007bff;
    background-color: white;
    color: #007bff;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s ease;
}

.view-btn:hover {
    background-color: #007bff;
    color: white;
}

.layers-list {
    max-height: 300px;
    overflow-y: auto;
}

.layer-item {
    padding: 12px;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    margin-bottom: 10px;
    background-color: #f8f9fa;
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
}

.layer-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    margin-bottom: 10px;
}

.layer-label input[type="checkbox"] {
    margin-right: 8px;
}

.layer-name {
    font-weight: 500;
    color: #495057;
}

.opacity-control {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}

.opacity-label {
    font-size: 12px;
    color: #6c757d;
    min-width: 50px;
    flex-shrink: 0;
}

.opacity-slider {
    flex: 1;
    min-width: 0;
    height: 4px;
    background: #ddd;
    outline: none;
    border-radius: 2px;
}

.opacity-value {
    font-size: 12px;
    color: #495057;
    font-weight: 500;
    min-width: 40px;
    flex-shrink: 0;
    text-align: right;
}

.no-layers {
    text-align: center;
    color: #6c757d;
    font-style: italic;
    padding: 20px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #f0f0f0;
}

.info-label {
    font-weight: 500;
    color: #495057;
}

.info-value {
    color: #6c757d;
}

/* 滚动条样式 */
.model-control-panel::-webkit-scrollbar,
.layers-list::-webkit-scrollbar {
    width: 6px;
}

.model-control-panel::-webkit-scrollbar-track,
.layers-list::-webkit-scrollbar-track {
    background: #f1f1f1;
}

.model-control-panel::-webkit-scrollbar-thumb,
.layers-list::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.model-control-panel::-webkit-scrollbar-thumb:hover,
.layers-list::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>