<template>
    <div id="app">
        <!-- 头部导航 -->
        <AppHeader :active-tab="currentTab" @tab-changed="handleTabChange" />

        <!-- 主要内容区域 -->
        <div class="main-content">
            <!-- 模型可视化页面 -->
            <div v-show="currentTab === 'model'" class="model-page">
                <ModelControlPanel :model-loaded="modelLoaded" :loading="loading" :layers="modelLayers"
                    :model-info="modelInfo" @load-model="handleLoadModel" @clear-model="handleClearModel"
                    @reset-camera="handleResetCamera" @find-model="handleFindModel"
                    @toggle-wireframe="handleToggleWireframe" @update-edge-color="handleUpdateEdgeColor"
                    @set-view="handleSetView" @toggle-layer-visibility="handleToggleLayerVisibility"
                    @update-layer-opacity="handleUpdateLayerOpacity" />

                <div class="viewer-container">
                    <ModelViewer ref="modelViewer" @loading-start="loading = true" @loading-end="loading = false"
                        @loading-progress="handleLoadingProgress" @loading-error="handleLoadingError"
                        @model-loaded="handleModelLoaded" @model-cleared="handleModelCleared" />

                    <!-- 加载状态显示 -->
                    <div v-if="loading" class="loading-overlay">
                        <div class="loading-content">
                            <div class="loading-spinner"></div>
                            <p>正在加载模型... {{ loadingProgress }}%</p>
                        </div>
                    </div>

                    <!-- 错误提示 -->
                    <div v-if="errorMessage" class="error-overlay">
                        <div class="error-content">
                            <h3>加载失败</h3>
                            <p>{{ errorMessage }}</p>
                            <button @click="errorMessage = ''" class="close-btn">关闭</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 其他页面（预留） -->
            <div v-show="currentTab === 'upload'" class="page-placeholder">
                <h2>数据上传功能</h2>
                <p>此功能正在开发中...</p>
            </div>

            <div v-show="currentTab === 'process'" class="page-placeholder">
                <h2>数据处理功能</h2>
                <p>此功能正在开发中...</p>
            </div>

            <div v-show="currentTab === 'settings'" class="page-placeholder">
                <h2>系统设置</h2>
                <p>此功能正在开发中...</p>
            </div>
        </div>
    </div>
</template>

<script>
import AppHeader from './components/AppHeader.vue'
import ModelControlPanel from './components/ModelControlPanel.vue'
import ModelViewer from './components/ModelViewer.vue'

export default {
    name: 'App',
    components: {
        AppHeader,
        ModelControlPanel,
        ModelViewer
    },
    data() {
        return {
            currentTab: 'model',
            modelLoaded: false,
            loading: false,
            loadingProgress: 0,
            errorMessage: '',
            modelLayers: [],
            modelInfo: null
        }
    },
    methods: {
        /**
         * 处理标签页切换
         * @param {string} tabName - 新的标签页名称
         */
        handleTabChange(tabName) {
            this.currentTab = tabName;
        },

        /**
         * 处理模型加载请求
         */
        handleLoadModel() {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.loadModel();
            }
        },

        /**
         * 处理模型清除请求
         */
        handleClearModel() {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.clearModel();
            }
        },

        /**
         * 处理相机重置请求
         */
        handleResetCamera() {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.resetCamera();
            }
        },

        /**
         * 处理查找模型请求
         */
        handleFindModel() {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.findModel();
            }
        },

        /**
         * 处理边缘线切换
         * @param {boolean} show - 是否显示边缘线
         */
        handleToggleWireframe(show) {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.toggleWireframe(show);
            }
        },

        /**
         * 处理边缘线颜色更新
         * @param {number} color - 新的颜色值
         */
        handleUpdateEdgeColor(color) {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.setEdgeColor(color);
            }
        },

        /**
         * 处理视角设置
         * @param {string} viewType - 视角类型
         */
        handleSetView(viewType) {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.setView(viewType);
            }
        },

        /**
         * 处理地层可见性切换
         * @param {Object} data - 包含layerId和visible的对象
         */
        handleToggleLayerVisibility(data) {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.toggleLayerVisibility(data.layerId, data.visible);
            }
        },

        /**
         * 处理地层透明度更新
         * @param {Object} data - 包含layerId和opacity的对象
         */
        handleUpdateLayerOpacity(data) {
            if (this.$refs.modelViewer) {
                this.$refs.modelViewer.updateLayerOpacity(data.layerId, data.opacity);
            }
        },

        /**
         * 处理加载进度更新
         * @param {number} progress - 加载进度百分比
         */
        handleLoadingProgress(progress) {
            this.loadingProgress = Math.round(progress);
        },

        /**
         * 处理加载错误
         * @param {string} errorMsg - 错误信息
         */
        handleLoadingError(errorMsg) {
            this.errorMessage = errorMsg;
            this.loading = false;
        },

        /**
         * 处理模型加载完成
         * @param {Object} data - 包含layers和modelInfo的对象
         */
        handleModelLoaded(data) {
            this.modelLoaded = true;
            this.modelLayers = data.layers;
            this.modelInfo = data.modelInfo;
            console.log('应用层接收到模型加载完成事件');
        },

        /**
         * 处理模型清除完成
         */
        handleModelCleared() {
            this.modelLoaded = false;
            this.modelLayers = [];
            this.modelInfo = null;
            console.log('应用层接收到模型清除完成事件');
        }
    }
}
</script>

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

#app {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    height: 100vh;
    overflow: hidden;
}

.main-content {
    padding-top: 60px;
    /* header高度 */
    height: 100vh;
    overflow: hidden;
}

.model-page {
    display: flex;
    height: calc(100vh - 60px);
}

.viewer-container {
    flex: 1;
    position: relative;
    overflow: hidden;
}

.page-placeholder {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    background-color: #f8f9fa;
}

.page-placeholder h2 {
    color: #495057;
    margin-bottom: 20px;
}

.page-placeholder p {
    color: #6c757d;
    font-size: 16px;
}

/* 加载状态覆盖层 */
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.loading-content {
    text-align: center;
    color: white;
}

.loading-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

/* 错误提示覆盖层 */
.error-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.error-content {
    background: white;
    padding: 30px;
    border-radius: 8px;
    text-align: center;
    max-width: 400px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.error-content h3 {
    color: #dc3545;
    margin-bottom: 15px;
}

.error-content p {
    color: #495057;
    margin-bottom: 20px;
}

.close-btn {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.close-btn:hover {
    background-color: #0056b3;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .model-page {
        flex-direction: column;
    }

    .main-content {
        padding-top: 60px;
    }
}
</style>
