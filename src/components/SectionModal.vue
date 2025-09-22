<template>
    <div v-if="visible" class="section-modal-overlay" @click="handleOverlayClick">
        <div class="section-modal" @click.stop>
            <div class="section-modal-header">
                <h3>剖面视图</h3>
                <button class="close-btn" @click="close">&times;</button>
            </div>
            
            <div class="section-modal-content">
                <div v-if="loading" class="loading">
                    正在生成剖面...
                </div>
                <div v-else-if="sectionData" class="section-container">
                    <!-- 左侧：剖面图显示区域 -->
                    <div class="section-left">
                        <div class="section-svg" v-html="currentSvg"></div>
                    </div>
                    
                    <!-- 右侧：控制面板和信息 -->
                    <div class="section-right">
                        <!-- 显示控制选项 -->
                        <div class="control-panel">
                            <h4>显示控制</h4>
                            <div class="control-options">
                                <label class="control-checkbox">
                                    <input type="checkbox" v-model="showLayerColors" @change="updateSectionDisplay" />
                                    显示地层颜色
                                </label>
                                <label class="control-checkbox">
                                    <input type="checkbox" v-model="showWireframe" @change="updateSectionDisplay" />
                                    显示线框
                                </label>
                            </div>
                        </div>
                        
                        <!-- 剖面信息 -->
                        <div class="section-info">
                            <h4>剖面信息</h4>
                            <div class="info-content">
                                <p><strong>剖面位置：</strong> {{ sectionData.position }}</p>
                                <p><strong>剖面法线：</strong> {{ sectionData.normal }}</p>
                                <p><strong>交点数量：</strong> {{ sectionData.intersectionCount }}</p>
                                <p><strong>生成时间：</strong> {{ sectionData.timestamp }}</p>
                            </div>
                        </div>
                        
                        <!-- 导出控制 -->
                        <div class="export-panel">
                            <h4>导出选项</h4>
                            <div class="export-buttons">
                                <button 
                                    @click="exportSection('png')" 
                                    :disabled="!sectionData || loading"
                                    class="export-btn">
                                    导出 PNG
                                </button>
                                <button 
                                    @click="exportSection('svg')" 
                                    :disabled="!sectionData || loading"
                                    class="export-btn">
                                    导出 SVG
                                </button>
                                <button 
                                    @click="exportSection('json')" 
                                    :disabled="!sectionData || loading"
                                    class="export-btn">
                                    导出数据
                                </button>
                            </div>
                        </div>
                        
                        <!-- 操作按钮 -->
                        <div class="action-panel">
                            <button @click="refreshSection" :disabled="loading" class="refresh-btn">
                                刷新剖面
                            </button>
                        </div>
                    </div>
                </div>
                <div v-else class="no-data">
                    暂无剖面数据
                </div>
            </div>
            
            <div class="section-modal-footer">
                <button @click="close" class="close-footer-btn">
                    关闭
                </button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'SectionModal',
    data() {
        return {
            visible: false,
            loading: false,
            sectionData: null,
            showLayerColors: true,
            showWireframe: false,
            currentSvg: ''
        }
    },
    mounted() {
        // 监听显示剖面模态窗口的事件
        this.$eventBus.$on('show-section-modal', this.showModal);
        this.$eventBus.$on('section-data-ready', this.setSectionData);
    },
    beforeDestroy() {
        this.$eventBus.$off('show-section-modal', this.showModal);
        this.$eventBus.$off('section-data-ready', this.setSectionData);
    },
    methods: {
        /**
         * 显示模态窗口
         */
        showModal(data = null) {
            this.visible = true;
            this.loading = true;
            this.sectionData = null;
            
            // 如果有数据直接显示，否则请求生成
            if (data) {
                this.setSectionData(data);
            } else {
                // 请求生成剖面数据
                this.$eventBus.$emit('generate-section');
            }
        },

        /**
         * 设置剖面数据
         */
        setSectionData(data) {
            console.log('收到剖面数据:', data);
            this.loading = false;
            this.sectionData = data;
            this.updateSectionDisplay();
        },

        /**
         * 更新剖面显示
         */
        updateSectionDisplay() {
            if (!this.sectionData) return;
            
            // 根据控制选项更新SVG显示
            if (this.showLayerColors && this.sectionData.svgColored) {
                this.currentSvg = this.sectionData.svgColored;
            } else if (this.showWireframe && this.sectionData.svg) {
                this.currentSvg = this.sectionData.svg;
            } else {
                this.currentSvg = this.sectionData.svg || '';
            }
        },

        /**
         * 关闭模态窗口
         */
        close() {
            this.visible = false;
            this.sectionData = null;
        },

        /**
         * 点击遮罩层关闭
         */
        handleOverlayClick() {
            this.close();
        },

        /**
         * 刷新剖面
         */
        refreshSection() {
            this.loading = true;
            this.sectionData = null;
            this.$eventBus.$emit('generate-section');
        },

        /**
         * 导出剖面
         */
        exportSection(format) {
            if (!this.sectionData) return;
            
            this.$eventBus.$emit('export-section', {
                format: format,
                data: this.sectionData
            });
        }
    }
}
</script>

<style scoped>
.section-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.section-modal {
    background: white;
    border-radius: 8px;
    width: 95%;
    max-width: 1400px;
    height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.section-modal-header {
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

.section-modal-header h3 {
    margin: 0;
    color: #333;
}

.close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
    width: 30px;
    height: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
    transition: all 0.2s;
}

.close-btn:hover {
    background: #f0f0f0;
    color: #333;
}

.section-modal-content {
    flex: 1;
    overflow: hidden;
    padding: 0;
    display: flex;
    flex-direction: column;
}

.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #666;
    font-size: 16px;
}

.section-container {
    display: flex;
    height: 100%;
    overflow: hidden;
}

/* 左侧剖面图区域 */
.section-left {
    flex: 2;
    padding: 20px;
    display: flex;
    flex-direction: column;
}

.section-svg {
    flex: 1;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 15px;
    background: #fafafa;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: auto;
    min-height: 400px;
}

.section-svg >>> svg {
    max-width: 100%;
    max-height: 100%;
    height: auto;
    width: auto;
}

/* 右侧控制面板区域 */
.section-right {
    flex: 1;
    background: #f8f9fa;
    border-left: 1px solid #e9ecef;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    overflow-y: auto;
    min-width: 300px;
}

.control-panel,
.section-info,
.export-panel,
.action-panel {
    background: white;
    border-radius: 6px;
    padding: 16px;
    border: 1px solid #e9ecef;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.control-panel h4,
.section-info h4,
.export-panel h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.control-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.info-content p {
    margin: 8px 0;
    font-size: 13px;
    color: #666;
    line-height: 1.4;
}

.info-content strong {
    color: #333;
}

.export-buttons {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.no-data {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #999;
    font-size: 16px;
}

.section-modal-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    flex-shrink: 0;
    background: #fafafa;
}

.close-footer-btn {
    padding: 10px 20px;
    border: 1px solid #6c757d;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    color: #6c757d;
}

.close-footer-btn:hover {
    background: #6c757d;
    color: white;
}

.export-btn,
.refresh-btn {
    padding: 8px 16px;
    border: 1px solid #007bff;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
    color: #007bff;
    width: 100%;
    text-align: center;
}

.export-btn:hover,
.refresh-btn:hover {
    background: #007bff;
    color: white;
}

.refresh-btn {
    background: #28a745;
    border-color: #28a745;
    color: white;
    font-weight: 500;
}

.refresh-btn:hover {
    background: #218838;
    border-color: #218838;
}

.export-btn:disabled,
.refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.export-btn:disabled:hover,
.refresh-btn:disabled:hover {
    background: white;
    border-color: #ddd;
    color: #6c757d;
}

.control-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    cursor: pointer;
    user-select: none;
    color: #333;
}

.control-checkbox input[type="checkbox"] {
    margin: 0;
    transform: scale(1.1);
    accent-color: #007bff;
}

.no-data {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #999;
    font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
    .section-modal {
        width: 98%;
        height: 90vh;
    }
    
    .section-right {
        min-width: 280px;
    }
}

@media (max-width: 768px) {
    .section-modal {
        width: 100%;
        height: 100vh;
        border-radius: 0;
    }
    
    .section-container {
        flex-direction: column;
    }
    
    .section-left {
        flex: 1.5;
        padding: 15px;
    }
    
    .section-right {
        flex: 1;
        border-left: none;
        border-top: 1px solid #e9ecef;
        min-width: auto;
        padding: 15px;
    }
    
    .section-svg {
        min-height: 250px;
    }
    
    .export-buttons {
        flex-direction: row;
        gap: 8px;
    }
    
    .export-btn {
        font-size: 12px;
        padding: 6px 12px;
    }
}
</style>