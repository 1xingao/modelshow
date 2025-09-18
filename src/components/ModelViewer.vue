<template>
    <div class="model-viewer" ref="container"></div>
</template>

<script>
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';

export default {
    name: 'ModelViewer',
    data() {
        return {
            scene: null,
            camera: null,
            renderer: null,
            controls: null,
            model: null,
            modelLayers: [],
            wireframeMode: false,
            originalMaterials: new Map(),
            boundingBox: null,
            animationId: null,
            axesHelper: null,
            edgeLines: [], // 存储边缘线对象
            edgeColor: 0x000000, // 统一边缘线颜色（黑色）
            showEdges: false, // 控制边缘线显示
            // 坐标轴相关
            coordinateBox: null, // 坐标轴包围盒
            coordinateLabels: [], // 坐标轴标签
            showCoordinateAxis: false, // 控制坐标轴显示
            axisColor: 0x333333, // 坐标轴颜色
            labelRenderer: null // 文字渲染器
        }
    },
    mounted() {
        this.initThreeJS();
        this.animate();
        window.addEventListener('resize', this.handleResize);
        
        // 监听来自控制面板的事件
        this.$eventBus.$on('load-model', this.loadModel);
        this.$eventBus.$on('clear-model', this.clearModel);
        this.$eventBus.$on('reset-camera', this.resetCamera);
        this.$eventBus.$on('find-model', this.findModel);
        this.$eventBus.$on('toggle-wireframe', this.toggleWireframe);
        this.$eventBus.$on('update-edge-color', this.setEdgeColor);
        this.$eventBus.$on('set-view', this.setView);
        this.$eventBus.$on('toggle-layer-visibility', this.handleToggleLayerVisibility);
        this.$eventBus.$on('update-layer-opacity', this.handleUpdateLayerOpacity);
        this.$eventBus.$on('toggle-coordinate-axis', this.toggleCoordinateAxis);
        this.$eventBus.$on('update-axis-color', this.setAxisColor);
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize);
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        // 清理事件监听器
        this.$eventBus.$off('load-model', this.loadModel);
        this.$eventBus.$off('clear-model', this.clearModel);
        this.$eventBus.$off('reset-camera', this.resetCamera);
        this.$eventBus.$off('find-model', this.findModel);
        this.$eventBus.$off('toggle-wireframe', this.toggleWireframe);
        this.$eventBus.$off('update-edge-color', this.setEdgeColor);
        this.$eventBus.$off('set-view', this.setView);
        this.$eventBus.$off('toggle-layer-visibility', this.handleToggleLayerVisibility);
        this.$eventBus.$off('update-layer-opacity', this.handleUpdateLayerOpacity);
        this.$eventBus.$off('toggle-coordinate-axis', this.toggleCoordinateAxis);
        this.$eventBus.$off('update-axis-color', this.setAxisColor);
        
        this.cleanup();
    },
    methods: {
        /**
         * 初始化Three.js场景
         */
        initThreeJS() {
            const container = this.$refs.container;
            const width = container.clientWidth;
            const height = container.clientHeight;

            // 创建场景（参照备份文件）
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0xfafafa);

            // 创建相机（参照备份文件的初始设置）
            this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
            this.camera.position.set(10, 10, 10);

            // 创建渲染器（参照备份文件 - 添加对数深度缓冲）
            this.renderer = new THREE.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true });
            this.renderer.setClearColor(0xfafafa);
            this.renderer.setSize(width, height);
            // 不启用阴影，简化渲染
            container.appendChild(this.renderer.domElement);

            // 创建CSS2D渲染器用于坐标轴标签
            this.labelRenderer = new CSS2DRenderer();
            this.labelRenderer.setSize(width, height);
            this.labelRenderer.domElement.style.position = 'absolute';
            this.labelRenderer.domElement.style.top = '0px';
            this.labelRenderer.domElement.style.pointerEvents = 'none';
            container.appendChild(this.labelRenderer.domElement);

            // 创建控制器（优化为360度旋转）
            this.controls = new OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.2; // 减少阻尼，让操作更灵敏
            this.controls.screenSpacePanning = false;
            this.controls.minDistance = 1;
            this.controls.maxDistance = 1000;
            // 移除极角限制，允许360度旋转
            this.controls.minPolarAngle = 0;
            this.controls.maxPolarAngle = Math.PI * 2;
            // 允许无限制旋转
            this.controls.enableRotate = true;
            this.controls.rotateSpeed = 1.0;

            // 添加光源
            this.setupLights();

            // 添加坐标轴辅助器（参照备份文件）
            this.axesHelper = new THREE.AxesHelper(100);
            this.scene.add(this.axesHelper);

            // 添加网格辅助器（参照备份文件 - 更淡的颜色）
            const gridHelper = new THREE.GridHelper(20, 20, 0xdddddd, 0xf0f0f0);
            this.scene.add(gridHelper);

            // 添加测试立方体来验证渲染
            this.addTestCube();
        },

        /**
         * 设置光源（参照备份文件 - 使用环境光避免阴影问题）
         */
        setupLights() {
            // 使用强环境光，避免阴影和光照复杂性（参照备份文件）
            const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
            this.scene.add(ambientLight);

            console.log('光源设置完成 - 使用纯环境光照明');
        },

        /**
         * 添加测试立方体
         */
        addTestCube() {
            const geometry = new THREE.BoxGeometry(10, 10, 10);
            const material = new THREE.MeshStandardMaterial({
                color: 0x00ff00,
                wireframe: false
            });
            const cube = new THREE.Mesh(geometry, material);
            cube.position.set(30, 5, 0);
            cube.name = 'testCube';
            this.scene.add(cube);
            console.log('测试立方体已添加');
        },

        /**
         * 移除测试立方体
         */
        removeTestCube() {
            const cube = this.scene.getObjectByName('testCube');
            if (cube) {
                this.scene.remove(cube);
                cube.geometry.dispose();
                cube.material.dispose();
                console.log('测试立方体已移除');
            }
        },

        /**
         * 动画循环
         */
        animate() {
            this.animationId = requestAnimationFrame(this.animate);

            if (this.controls) {
                this.controls.update();
            }

            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
                // 渲染坐标轴标签
                if (this.labelRenderer) {
                    this.labelRenderer.render(this.scene, this.camera);
                }
            }
        },

        /**
         * 加载GLTF模型
         * @param {string} modelPath - 模型文件路径
         */
        async loadModel(modelPath = './model_gltf/output_model.gltf') {
            try {
                this.$eventBus.$emit('loading-start');

                const loader = new GLTFLoader();
                const gltf = await this.loadGLTF(loader, modelPath);

                // 清除之前的模型
                this.clearModel();

                this.model = gltf.scene;

                // 确保模型可见
                this.model.visible = true;

                // 计算模型包围盒（在添加到场景前）
                const box = new THREE.Box3().setFromObject(this.model);
                console.log('模型包围盒:', {
                    min: box.min,
                    max: box.max,
                    size: box.getSize(new THREE.Vector3()),
                    center: box.getCenter(new THREE.Vector3())
                });

                // 如果模型太小，放大它
                const size = box.getSize(new THREE.Vector3());
                const maxDimension = Math.max(size.x, size.y, size.z);
                if (maxDimension < 1) {
                    const scale = 10 / maxDimension;
                    this.model.scale.setScalar(scale);
                    console.log('模型太小，已放大', scale, '倍');

                    // 重新计算放大后的包围盒
                    box.setFromObject(this.model);
                }

                this.scene.add(this.model);
                console.log('模型已添加到场景');

                // 处理模型中的所有网格（参照备份文件逻辑）
                const meshes = [];
                this.model.traverse((child) => {
                    if (child.isMesh) {
                        meshes.push(child);
                    }
                });

                console.log(`找到 ${meshes.length} 个网格对象`);

                if (meshes.length === 0) {
                    console.warn('GLTF场景中没有找到任何网格对象');
                    return;
                }

                // 为每个网格优化材质和可见性
                meshes.forEach((mesh, index) => {
                    mesh.visible = true;

                    console.log('处理mesh:', mesh.name || `网格${index + 1}`, '原材质:', mesh.material);

                    // 优化材质 - 使用MeshBasicMaterial避免光照问题
                    const originalMaterial = mesh.material;
                    const layerColor = this.generateLayerColor(index);

                    const basicMaterial = new THREE.MeshBasicMaterial({
                        color: layerColor,
                        transparent: true,
                        opacity: 1.0,
                        side: THREE.DoubleSide
                    });

                    // 如果原材质有纹理，保留纹理
                    if (originalMaterial && originalMaterial.map) {
                        basicMaterial.map = originalMaterial.map;
                    }

                    mesh.material = basicMaterial;

                    // 为每个网格创建对应的边缘线
                    const edges = new THREE.EdgesGeometry(mesh.geometry);
                    const edgesMaterial = new THREE.LineBasicMaterial({
                        color: this.edgeColor,
                        transparent: true,
                        opacity: 0.8
                    });
                    const edgeLines = new THREE.LineSegments(edges, edgesMaterial);
                    edgeLines.visible = this.showEdges;

                    // 将边缘线存储在网格的userData中，建立关联
                    mesh.userData.edgeLines = edgeLines;

                    // 将边缘线添加到模型中
                    this.model.add(edgeLines);
                    this.edgeLines.push(edgeLines);

                    console.log('为mesh设置了新材质和边缘线:', mesh.name, '颜色:', layerColor.toString(16));
                });

                // 解析地层（在材质处理之后）
                this.parseLayers(this.model);

                // 计算包围盒并调整相机
                this.fitCameraToModel();

                // 计算模型信息
                const modelInfo = this.calculateModelInfo();

                this.$eventBus.$emit('model-loaded', {
                    layers: this.modelLayers,
                    modelInfo: modelInfo
                });

                // 移除测试立方体
                this.removeTestCube();

                console.log('模型加载成功，共有', this.modelLayers.length, '个地层');
            } catch (error) {
                console.error('模型加载失败:', error);
                console.error('错误详情:', error);
                this.$eventBus.$emit('loading-error', `模型加载失败: ${error.message}`);
            } finally {
                this.$eventBus.$emit('loading-end');
            }
        },

        /**
         * 使用Promise封装GLTF加载器
         * @param {GLTFLoader} loader - GLTF加载器实例
         * @param {string} path - 模型路径
         * @returns {Promise} GLTF对象
         */
        loadGLTF(loader, path) {
            return new Promise((resolve, reject) => {
                console.log('开始加载GLTF文件:', path);
                loader.load(
                    path,
                    (gltf) => {
                        console.log('GLTF文件加载成功:', gltf);
                        resolve(gltf);
                    },
                    (progress) => {
                        const percent = progress.total > 0 ? (progress.loaded / progress.total) * 100 : 0;
                        console.log('加载进度:', percent + '%', progress);
                        this.$eventBus.$emit('loading-progress', percent);
                    },
                    (error) => {
                        console.error('GLTF加载错误:', error);
                        reject(error);
                    }
                );
            });
        },

        /**
         * 解析模型中的地层
         * @param {THREE.Object3D} model - 3D模型对象
         */
        parseLayers(model) {
            this.modelLayers = [];
            this.originalMaterials.clear();

            model.traverse((child) => {
                if (child.isMesh) {
                    const layerName = child.name || `Layer_${this.modelLayers.length + 1}`;

                    // 保存原始材质
                    if (child.material) {
                        this.originalMaterials.set(child.uuid, child.material.clone());
                    }

                    const layer = {
                        id: child.uuid,
                        name: layerName,
                        mesh: child,
                        visible: true,
                        opacity: 1.0
                    };

                    this.modelLayers.push(layer);
                }
            });

            console.log(`解析到 ${this.modelLayers.length} 个地层`);
        },

        /**
         * 计算模型信息
         * @returns {Object} 模型统计信息
         */
        calculateModelInfo() {
            let totalVertices = 0;
            let totalFaces = 0;

            if (this.model) {
                this.model.traverse((child) => {
                    if (child.isMesh && child.geometry) {
                        const geometry = child.geometry;
                        if (geometry.attributes.position) {
                            totalVertices += geometry.attributes.position.count;
                        }
                        if (geometry.index) {
                            totalFaces += geometry.index.count / 3;
                        }
                    }
                });
            }

            return {
                fileName: 'output_model.gltf',
                vertices: totalVertices.toLocaleString(),
                faces: Math.floor(totalFaces).toLocaleString()
            };
        },

        /**
         * 调整相机以适应模型（参照备份文件的逻辑）
         */
        fitCameraToModel() {
            if (!this.model) return;

            // 计算所有网格的包围盒
            const box = new THREE.Box3();

            // 确保每个mesh都计算了包围盒
            this.model.traverse((child) => {
                if (child.isMesh && child.geometry) {
                    child.geometry.computeBoundingBox();
                    box.expandByObject(child);
                }
            });

            this.boundingBox = box;

            console.log('边界框:', box);
            console.log('边界框是否为空:', box.isEmpty());

            if (box.isEmpty()) {
                console.warn('边界框为空，无法调整相机');
                this.camera.position.set(50, 50, 50);
                this.camera.lookAt(0, 0, 0);
                this.controls.target.set(0, 0, 0);
                this.controls.update();
                return;
            }

            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);

            console.log('模型信息:', {
                center: center,
                size: size,
                maxDimension: maxDim
            });

            // 计算相机距离（参照备份文件的计算方式）
            const fov = this.camera.fov * (Math.PI / 180);
            const cameraDistance = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 2.0;

            // 设置相机位置（默认底视图 - 从下往上看）
            this.camera.position.set(
                center.x,
                center.y - cameraDistance,
                center.z
            );

            // 设置相机目标
            this.controls.target.copy(center);
            this.camera.lookAt(center);

            // 更新相机的near和far平面
            this.camera.near = cameraDistance / 100;
            this.camera.far = cameraDistance * 10;
            this.camera.updateProjectionMatrix();

            // 更新控制器约束
            this.controls.minDistance = cameraDistance * 0.1;
            this.controls.maxDistance = cameraDistance * 5;

            // 更新控制器
            this.controls.update();

            console.log('相机调整完成:', {
                center: center,
                size: size,
                maxDimension: maxDim,
                cameraDistance: cameraDistance,
                cameraPosition: this.camera.position.clone(),
                targetPosition: this.controls.target.clone(),
                near: this.camera.near,
                far: this.camera.far
            });

            // 如果坐标轴开启，则创建坐标轴
            if (this.showCoordinateAxis) {
                this.createCoordinateAxis();
            }

            // 添加延时检查
            setTimeout(() => {
                this.checkModelVisibility();
            }, 100);
        },

        /**
         * 检查模型是否可见
         */
        checkModelVisibility() {
            if (!this.model) return;

            let visibleMeshes = 0;
            let totalMeshes = 0;

            this.model.traverse((child) => {
                if (child.isMesh) {
                    totalMeshes++;
                    if (child.visible) {
                        visibleMeshes++;
                    }
                    console.log('Mesh信息:', {
                        name: child.name,
                        visible: child.visible,
                        position: child.position,
                        scale: child.scale,
                        material: child.material ? child.material.constructor.name : 'no material'
                    });
                }
            });

            console.log(`模型可见性检查: ${visibleMeshes}/${totalMeshes} 个网格可见`);

            if (visibleMeshes === 0) {
                console.warn('没有可见的网格！模型可能存在问题。');
            }
        },

        /**
         * 查找并定位到模型
         */
        findModel() {
            if (!this.model) {
                console.log('没有模型需要查找');
                return;
            }

            console.log('开始查找模型...');

            // 获取模型的包围盒
            const box = new THREE.Box3().setFromObject(this.model);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());

            console.log('查找模型信息:', {
                center: center,
                size: size,
                min: box.min,
                max: box.max
            });

            if (box.isEmpty()) {
                console.warn('模型包围盒为空');
                return;
            }

            // 使用更保守的距离设置
            const maxDimension = Math.max(size.x, size.y, size.z);
            const distance = maxDimension > 0 ? maxDimension * 5 : 50;

            // 尝试不同的相机位置来查找模型
            const positions = [
                // 前上右
                { x: center.x + distance, y: center.y + distance, z: center.z + distance },
                // 后上左  
                { x: center.x - distance, y: center.y + distance, z: center.z - distance },
                // 正上方
                { x: center.x, y: center.y + distance * 2, z: center.z },
                // 正前方
                { x: center.x, y: center.y, z: center.z + distance * 2 },
                // 侧面
                { x: center.x + distance * 2, y: center.y, z: center.z }
            ];

            let currentIndex = 0;

            const tryNextPosition = () => {
                if (currentIndex >= positions.length) {
                    console.log('已尝试所有位置');
                    return;
                }

                const pos = positions[currentIndex];
                this.camera.position.set(pos.x, pos.y, pos.z);
                this.camera.lookAt(center);
                this.controls.target.copy(center);
                this.controls.update();

                console.log(`尝试位置 ${currentIndex + 1}: `, pos);
                currentIndex++;

                // 每2秒切换到下一个位置
                if (currentIndex < positions.length) {
                    setTimeout(tryNextPosition, 2000);
                }
            };

            tryNextPosition();
        },

        /**
         * 清除模型
         */
        clearModel() {
            if (this.model) {
                this.scene.remove(this.model);

                // 清理几何体和材质
                this.model.traverse((child) => {
                    if (child.isMesh) {
                        if (child.geometry) {
                            child.geometry.dispose();
                        }
                        if (child.material) {
                            if (Array.isArray(child.material)) {
                                child.material.forEach(material => material.dispose());
                            } else {
                                child.material.dispose();
                            }
                        }
                    }
                });

                this.model = null;
                this.modelLayers = [];
                this.originalMaterials.clear();

                // 清除边缘线 - 通过地层关联清除
                this.modelLayers.forEach(layer => {
                    if (layer.mesh && layer.mesh.userData.edgeLines) {
                        const edgeLines = layer.mesh.userData.edgeLines;
                        if (edgeLines.geometry) edgeLines.geometry.dispose();
                        if (edgeLines.material) edgeLines.material.dispose();
                    }
                });
                this.edgeLines = [];

                console.log('模型已清除');

                // 重新添加测试立方体
                this.addTestCube();

                this.$eventBus.$emit('model-cleared');
            }
        },

        /**
         * 重置相机位置
         */
        resetCamera() {
            if (this.model && this.boundingBox) {
                this.fitCameraToModel();
            } else {
                // 默认位置 - 使用更远的距离
                this.camera.position.set(100, 100, 100);
                this.controls.target.set(0, 0, 0);
                this.controls.update();
            }
        },

        /**
         * 切换边缘线模式
         * @param {boolean} show - 是否显示边缘线
         */
        toggleWireframe(show) {
            this.showEdges = show;

            // 遍历所有地层，只对可见地层显示边缘线
            this.modelLayers.forEach(layer => {
                if (layer.mesh && layer.mesh.userData.edgeLines) {
                    // 边缘线的可见性 = 边缘线开关 AND 地层可见性
                    layer.mesh.userData.edgeLines.visible = show && layer.visible;
                }
            });
        },

        /**
         * 更改边缘线颜色
         * @param {number} color - 新的颜色值
         */
        setEdgeColor(color) {
            this.edgeColor = color;

            // 更新所有地层的边缘线颜色
            this.modelLayers.forEach(layer => {
                if (layer.mesh && layer.mesh.userData.edgeLines && layer.mesh.userData.edgeLines.material) {
                    layer.mesh.userData.edgeLines.material.color.setHex(color);
                }
            });
        },

        /**
         * 设置视角（参照备份文件的逻辑）
         * @param {string} viewType - 视角类型
         */
        setView(viewType) {
            if (!this.model || !this.boundingBox) {
                this.setDefaultViewAngle(viewType);
                return;
            }

            if (this.boundingBox.isEmpty()) {
                this.setDefaultViewAngle(viewType);
                return;
            }

            const center = this.boundingBox.getCenter(new THREE.Vector3());
            const size = this.boundingBox.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            const distance = maxDim * 2;

            let cameraPosition = new THREE.Vector3();

            switch (viewType) {
                case 'front':
                    // 正面 = 原来的底视图（从下往上看）
                    cameraPosition.set(center.x, center.y - distance, center.z);
                    break;
                case 'back':
                    // 背面 = 原来的顶视图（从上往下看）
                    cameraPosition.set(center.x, center.y + distance, center.z);
                    break;
                case 'left':
                    // 左侧视图
                    cameraPosition.set(center.x - distance, center.y, center.z);
                    break;
                case 'right':
                    // 右侧视图  
                    cameraPosition.set(center.x + distance, center.y, center.z);
                    break;
                case 'top':
                    // 顶视图 = 原来的前视图（从Z轴正方向看）
                    cameraPosition.set(center.x, center.y, center.z + distance);
                    break;
                case 'bottom':
                    // 底视图 = 原来的后视图（从Z轴负方向看）
                    cameraPosition.set(center.x, center.y, center.z - distance);
                    break;
                default:
                    // 默认等轴测视图
                    cameraPosition.set(
                        center.x + distance * 0.7,
                        center.y - distance * 0.7,
                        center.z + distance * 0.7
                    );
            }

            // 使用动画移动相机
            this.animateCameraTo(cameraPosition, center);
        },

        /**
         * 设置默认视角（当没有模型时）
         * @param {string} viewType - 视角类型
         */
        setDefaultViewAngle(viewType) {
            const distance = 50;
            let cameraPosition = new THREE.Vector3();
            const center = new THREE.Vector3(0, 0, 0);

            switch (viewType) {
                case 'front':
                    // 正面 = 从下往上看
                    cameraPosition.set(0, -distance, 0);
                    break;
                case 'back':
                    // 背面 = 从上往下看
                    cameraPosition.set(0, distance, 0);
                    break;
                case 'left':
                    cameraPosition.set(-distance, 0, 0);
                    break;
                case 'right':
                    cameraPosition.set(distance, 0, 0);
                    break;
                case 'top':
                    // 顶视图 = 从Z轴正方向看
                    cameraPosition.set(0, 0, distance);
                    break;
                case 'bottom':
                    // 底视图 = 从Z轴负方向看
                    cameraPosition.set(0, 0, -distance);
                    break;
                default:
                    cameraPosition.set(distance * 0.7, -distance * 0.7, distance * 0.7);
            }

            this.animateCameraTo(cameraPosition, center);
        },

        /**
         * 动画移动相机到目标位置
         * @param {THREE.Vector3} targetPosition - 目标位置
         * @param {THREE.Vector3} targetLookAt - 目标观察点
         */
        animateCameraTo(targetPosition, targetLookAt) {
            const startPosition = this.camera.position.clone();
            const startTarget = this.controls.target.clone();

            const duration = 1000; // 1秒动画
            const startTime = Date.now();

            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // 使用easeInOutQuad缓动函数
                const easeProgress = progress < 0.5
                    ? 2 * progress * progress
                    : 1 - Math.pow(-2 * progress + 2, 2) / 2;

                // 插值相机位置
                this.camera.position.lerpVectors(startPosition, targetPosition, easeProgress);
                this.controls.target.lerpVectors(startTarget, targetLookAt, easeProgress);

                this.camera.lookAt(this.controls.target);
                this.controls.update();

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            animate();
        },

        /**
         * 生成地层颜色
         * @param {number} index - 地层索引
         * @returns {number} 颜色值
         */
        generateLayerColor(index) {
            const colors = [
                0x8B4513, // 马鞍棕色
                0xDAA520, // 金麦色
                0x2E8B57, // 海绿色
                0x4682B4, // 钢蓝色
                0xD2691E, // 巧克力色
                0x9ACD32, // 黄绿色
                0xCD853F, // 秘鲁色
                0x20B2AA, // 浅海绿色
                0x778899, // 浅石板灰
                0xF0E68C  // 卡其色
            ];
            return colors[index % colors.length];
        },

        /**
         * 切换地层可见性
         * @param {string} layerId - 地层ID
         * @param {boolean} visible - 是否可见
         */
        toggleLayerVisibility(layerId, visible) {
            const layer = this.modelLayers.find(l => l.id === layerId);
            if (layer && layer.mesh) {
                // 设置网格可见性
                layer.mesh.visible = visible;
                layer.visible = visible;

                // 同时设置对应边缘线的可见性
                if (layer.mesh.userData.edgeLines) {
                    // 边缘线的可见性取决于：地层可见 AND 边缘线开关打开
                    layer.mesh.userData.edgeLines.visible = visible && this.showEdges;
                }
            }
        },

        /**
         * 更新地层透明度
         * @param {string} layerId - 地层ID
         * @param {number} opacity - 透明度值 (0-1)
         */
        updateLayerOpacity(layerId, opacity) {
            const layer = this.modelLayers.find(l => l.id === layerId);
            if (layer && layer.mesh && layer.mesh.material) {
                const material = layer.mesh.material;

                // 设置透明度
                if (opacity < 1) {
                    material.transparent = true;
                    material.opacity = opacity;
                } else {
                    material.transparent = false;
                    material.opacity = 1;
                }

                // 同时更新边缘线的透明度
                if (layer.mesh.userData.edgeLines && layer.mesh.userData.edgeLines.material) {
                    layer.mesh.userData.edgeLines.material.opacity = Math.min(opacity + 0.2, 1.0);
                }

                layer.opacity = opacity;
                material.needsUpdate = true;
            }
        },

        /**
         * 处理窗口大小变化
         */
        handleResize() {
            const container = this.$refs.container;
            const width = container.clientWidth;
            const height = container.clientHeight;

            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();

            this.renderer.setSize(width, height);
            
            if (this.labelRenderer) {
                this.labelRenderer.setSize(width, height);
            }
        },

        /**
         * 创建坐标轴包围盒和标签
         */
        createCoordinateAxis() {
            if (!this.model || !this.boundingBox) {
                console.warn('无法创建坐标轴：模型或包围盒不存在');
                return;
            }

            this.clearCoordinateAxis();

            const box = this.boundingBox;
            const min = box.min;
            const max = box.max;
            const size = box.getSize(new THREE.Vector3());

            // 创建包围盒线框
            const boxGeometry = new THREE.BoxGeometry(size.x, size.y, size.z);
            const boxEdges = new THREE.EdgesGeometry(boxGeometry);
            const boxMaterial = new THREE.LineBasicMaterial({ 
                color: this.axisColor,
                transparent: true,
                opacity: 0.8
            });

            this.coordinateBox = new THREE.LineSegments(boxEdges, boxMaterial);
            this.coordinateBox.position.copy(box.getCenter(new THREE.Vector3()));
            this.scene.add(this.coordinateBox);

            // 创建坐标标签
            this.createAxisLabels(min, max, size);
        },

        /**
         * 创建坐标轴标签
         */
        createAxisLabels(min, max, size) {
            // 计算合适的刻度间隔
            const getTickInterval = (dimension) => {
                const magnitude = Math.floor(Math.log10(dimension));
                const normalized = dimension / Math.pow(10, magnitude);
                
                let interval;
                if (normalized <= 2) interval = 0.5;
                else if (normalized <= 5) interval = 1;
                else interval = 2;
                
                return interval * Math.pow(10, magnitude);
            };

            const xInterval = getTickInterval(size.x);
            const yInterval = getTickInterval(size.y);
            const zInterval = getTickInterval(size.z);

            // X轴标签 (沿着底部前边)
            this.createAxisTickLabels('x', min.x, max.x, xInterval, min.y, min.z);
            
            // Y轴标签 (沿着左侧前边)
            this.createAxisTickLabels('y', min.y, max.y, yInterval, min.x, min.z);
            
            // Z轴标签 (沿着左侧底边)
            this.createAxisTickLabels('z', min.z, max.z, zInterval, min.x, min.y);
        },

        /**
         * 创建单个轴的刻度标签
         */
        createAxisTickLabels(axis, minValue, maxValue, interval, fixedCoord1, fixedCoord2) {
            const start = Math.ceil(minValue / interval) * interval;
            const end = Math.floor(maxValue / interval) * interval;

            for (let value = start; value <= end; value += interval) {
                // 避免浮点数精度问题
                const roundedValue = Math.round(value / interval) * interval;
                
                const labelDiv = document.createElement('div');
                labelDiv.className = 'coordinate-label';
                labelDiv.textContent = roundedValue.toFixed(2);
                labelDiv.style.color = `#${this.axisColor.toString(16).padStart(6, '0')}`;
                labelDiv.style.fontSize = '12px';
                labelDiv.style.fontFamily = 'Arial, sans-serif';
                labelDiv.style.padding = '2px 4px';
                labelDiv.style.backgroundColor = 'rgba(0,0,0, 0)';
                labelDiv.style.borderRadius = '3px';
                labelDiv.style.pointerEvents = 'none';

                const label = new CSS2DObject(labelDiv);

                // 根据轴设置位置
                switch (axis) {
                    case 'x':
                        label.position.set(roundedValue, fixedCoord1, fixedCoord2);
                        break;
                    case 'y':
                        label.position.set(fixedCoord1, roundedValue, fixedCoord2);
                        break;
                    case 'z':
                        label.position.set(fixedCoord1, fixedCoord2, roundedValue);
                        break;
                }

                this.coordinateLabels.push(label);
                this.scene.add(label);
            }
        },

        /**
         * 切换坐标轴显示
         */
        toggleCoordinateAxis() {
            this.showCoordinateAxis = !this.showCoordinateAxis;
            
            if (this.showCoordinateAxis) {
                this.createCoordinateAxis();
            } else {
                this.clearCoordinateAxis();
            }

            this.$eventBus.$emit('coordinate-axis-changed', this.showCoordinateAxis);
        },

        /**
         * 设置坐标轴颜色
         */
        setAxisColor(color) {
            this.axisColor = color;
            
            // 更新现有坐标轴颜色
            if (this.coordinateBox && this.coordinateBox.material) {
                this.coordinateBox.material.color.setHex(color);
            }

            // 更新标签颜色
            this.coordinateLabels.forEach(label => {
                if (label.element) {
                    label.element.style.color = `#${color.toString(16).padStart(6, '0')}`;
                }
            });
        },

        /**
         * 清除坐标轴
         */
        clearCoordinateAxis() {
            // 清除包围盒
            if (this.coordinateBox) {
                this.scene.remove(this.coordinateBox);
                this.coordinateBox.geometry.dispose();
                this.coordinateBox.material.dispose();
                this.coordinateBox = null;
            }

            // 清除标签
            this.coordinateLabels.forEach(label => {
                this.scene.remove(label);
                if (label.element && label.element.parentNode) {
                    label.element.parentNode.removeChild(label.element);
                }
            });
            this.coordinateLabels = [];
        },

        /**
         * 处理地层可见性切换事件
         */
        handleToggleLayerVisibility(data) {
            this.toggleLayerVisibility(data.layerId, data.visible);
        },

        /**
         * 处理地层透明度更新事件
         */
        handleUpdateLayerOpacity(data) {
            this.updateLayerOpacity(data.layerId, data.opacity);
        },

        /**
         * 清理资源
         */
        cleanup() {
            if (this.renderer) {
                this.renderer.dispose();
            }

            if (this.labelRenderer && this.labelRenderer.domElement && this.labelRenderer.domElement.parentNode) {
                this.labelRenderer.domElement.parentNode.removeChild(this.labelRenderer.domElement);
            }

            if (this.model) {
                this.clearModel();
            }

            this.clearCoordinateAxis();

            // 清理几何体和材质
            this.originalMaterials.forEach(material => material.dispose());
            this.originalMaterials.clear();
        }
    }
}
</script>

<style scoped>
.model-viewer {
    width: 100%;
    height: 100%;
    position: relative;
    background-color: #f5f5f5;
}

.model-viewer canvas {
    display: block;
    width: 100% !important;
    height: 100% !important;
}
</style>

<style>
/* 坐标轴标签样式 - 不使用 scoped，因为这些是动态创建的 DOM 元素 */
.coordinate-label {
    font-family: Arial, sans-serif;
    font-size: 12px;
    font-weight: 500;
    text-align: center;
    white-space: nowrap;
    user-select: none;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.coordinate-label:hover {
    transform: scale(1.1);
    transition: transform 0.2s ease;
}
</style>