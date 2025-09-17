<template>
    <div class="model-viewer">
        <div class="viewer-container">
            <div id="three-container" class="three-container"></div>
            <div class="info-panel" v-if="showInfo">
                <h3>模型信息</h3>
                <div class="info-item">
                    <label>模型名称:</label>
                    <span>{{ modelInfo.name }}</span>
                </div>
                <div class="info-item">
                    <label>地层数量:</label>
                    <span>{{ modelInfo.layers }}</span>
                </div>
                <div class="info-item">
                    <label>顶点数量:</label>
                    <span>{{ modelInfo.vertices }}</span>
                </div>
                <div class="info-item">
                    <label>面数量:</label>
                    <span>{{ modelInfo.faces }}</span>
                </div>
            </div>
            <div class="loading" v-if="isLoading">
                <div class="loader"></div>
                <p>正在加载模型...</p>
            </div>
        </div>
        <div class="control-panel">
            <div class="panel-section">
                <h4>模型加载</h4>
                <div class="model-buttons">
                    <button @click="loadVTMModel" class="panel-btn">
                        加载VTM模型
                    </button>
                    <button @click="loadGLTFModel" class="panel-btn gltf-btn">
                        加载GLTF模型
                    </button>
                </div>
            </div>
            <div class="panel-section">
                <h4>视图控制</h4>
                <button @click="toggleInfo" class="panel-btn">
                    {{ showInfo ? '隐藏信息' : '显示信息' }}
                </button>
                <button @click="resetView" class="panel-btn">
                    重置视图
                </button>
                <button @click="toggleEdges" class="panel-btn">
                    {{ showEdges ? '隐藏边缘' : '显示边缘' }}
                </button>
                <button @click="toggleAxes" class="panel-btn">
                    {{ showAxes ? '隐藏坐标轴' : '显示坐标轴' }}
                </button>
            </div>
            <div class="panel-section">
                <h4>相机视角</h4>
                <div class="view-buttons">
                    <button @click="setViewAngle('front')" class="panel-btn view-btn">
                        前视图
                    </button>
                    <button @click="setViewAngle('back')" class="panel-btn view-btn">
                        后视图
                    </button>
                    <button @click="setViewAngle('left')" class="panel-btn view-btn">
                        左视图
                    </button>
                    <button @click="setViewAngle('right')" class="panel-btn view-btn">
                        右视图
                    </button>
                    <button @click="setViewAngle('top')" class="panel-btn view-btn">
                        俯视图
                    </button>
                    <button @click="setViewAngle('bottom')" class="panel-btn view-btn">
                        仰视图
                    </button>
                    <button @click="setViewAngle('isometric')" class="panel-btn view-btn">
                        等轴测
                    </button>
                </div>
            </div>
            <div class="panel-section" v-if="layers.length > 0">
                <h4>地层控制</h4>
                <div v-for="layer in layers" :key="layer.id" class="layer-item">
                    <input type="checkbox" :id="'layer-' + layer.id" v-model="layer.visible"
                        @change="toggleLayer(layer)">
                    <label :for="'layer-' + layer.id">{{ layer.name }}</label>
                    <input type="range" min="0" max="1" step="0.1" v-model="layer.opacity"
                        @input="updateLayerOpacity(layer)" class="opacity-slider">
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import vtpService from '@/services/vtpService'

export default {
    name: 'ModelViewer',
    data() {
        return {
            scene: null,
            camera: null,
            renderer: null,
            controls: null,
            isLoading: false,
            showInfo: true,
            modelInfo: {
                name: '未加载模型',
                layers: 0,
                vertices: 0,
                faces: 0
            },
            layers: [],
            layerMeshes: [],
            showEdges: false, // 控制是否显示边缘线
            showAxes: true, // 控制是否显示坐标轴
            axesHelper: null // 坐标轴对象
        }
    },
    mounted() {
        this.initThreeJS()
        this.animate()

        // 监听窗口大小变化
        window.addEventListener('resize', this.onWindowResize, false)
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.onWindowResize, false)
        if (this.renderer) {
            this.renderer.dispose()
        }
    },
    methods: {
        initThreeJS() {
            // 创建场景
            this.scene = new THREE.Scene()
            this.scene.background = new THREE.Color(0xfafafa)

            // 创建相机
            this.camera = new THREE.PerspectiveCamera(
                75,
                window.innerWidth / window.innerHeight,
                0.1,
                1000
            )
            this.camera.position.set(10, 10, 10)

            // 创建渲染器
            this.renderer = new THREE.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true })
            this.renderer.setClearColor(0xfafafa)
            const container = document.getElementById('three-container')
            if (container) {
                this.renderer.setSize(container.clientWidth, container.clientHeight)
                container.appendChild(this.renderer.domElement)
            }

            // 创建控制器
            this.controls = new OrbitControls(this.camera, this.renderer.domElement)
            this.controls.enableDamping = true
            this.controls.dampingFactor = 0.05
            this.controls.screenSpacePanning = false
            this.controls.minDistance = 1
            this.controls.maxDistance = 1000
            this.controls.maxPolarAngle = Math.PI

            // 添加环境光（无阴影的均匀照明）
            const ambientLight = new THREE.AmbientLight(0xffffff, 1.0)
            this.scene.add(ambientLight)

            // 添加网格 - 更淡的颜色
            const gridHelper = new THREE.GridHelper(20, 20, 0xdddddd, 0xf0f0f0)
            this.scene.add(gridHelper)

            // 添加坐标轴
            this.axesHelper = new THREE.AxesHelper(100)
            this.axesHelper.visible = this.showAxes
            this.scene.add(this.axesHelper)
        },
        async loadVTMModel() {
            try {
                this.isLoading = true
                this.clearCurrentModel()

                // 尝试加载VTM文件
                const vtmPath = '/model/output_model.vtm'
                const response = await fetch(vtmPath)

                if (!response.ok) {
                    throw new Error('VTM文件未找到')
                }

                const vtmData = await response.text()

                // 使用VTP服务解析VTM文件
                const vtpFiles = vtpService.parseVTMFile(vtmData)
                console.log(`找到 ${vtpFiles.length} 个地层文件`)

                if (vtpFiles.length === 0) {
                    throw new Error('VTM文件中未找到有效的VTP文件')
                }

                this.layers = vtpFiles

                // 使用VTP服务加载所有VTP文件
                const meshes = await vtpService.loadVTPFiles(vtpFiles, (progress) => {
                    console.log(`加载进度: ${progress.current}/${progress.total} - ${progress.layerName}`)
                })

                // 将网格添加到场景
                meshes.forEach(mesh => {
                    if (mesh) {
                        // 设置边缘线显示状态
                        if (mesh.userData.edges) {
                            mesh.userData.edges.visible = this.showEdges
                        }
                        this.scene.add(mesh)
                        this.layerMeshes.push(mesh)
                    }
                })

                // 计算模型统计信息
                const stats = vtpService.calculateModelStats(this.layerMeshes)
                this.modelInfo.name = 'VTM地质模型'
                this.modelInfo.layers = stats.layers
                this.modelInfo.vertices = stats.vertices
                this.modelInfo.faces = stats.faces

                // 调整相机视角
                if (this.layerMeshes.length > 0) {
                    this.fitCameraToModels(this.layerMeshes)
                }

                console.log('VTM模型加载完成')

            } catch (error) {
                console.error('加载VTM模型失败:', error)
                alert(`VTM模型加载失败: ${error.message}`)
            } finally {
                this.isLoading = false
            }
        },

        fitCameraToModels(meshes) {
            const box = new THREE.Box3()

            meshes.forEach(layerGroup => {
                if (layerGroup.userData.mesh) {
                    layerGroup.userData.mesh.geometry.computeBoundingBox()
                    box.expandByObject(layerGroup.userData.mesh)
                }
            })

            console.log('边界框:', box)
            console.log('边界框是否为空:', box.isEmpty())

            if (box.isEmpty()) {
                console.warn('边界框为空，无法调整相机')
                return
            }

            const center = box.getCenter(new THREE.Vector3())
            const size = box.getSize(new THREE.Vector3())
            const maxDim = Math.max(size.x, size.y, size.z)

            // 计算相机距离
            const fov = this.camera.fov * (Math.PI / 180)
            const cameraDistance = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 2.0

            // 设置相机位置
            this.camera.position.set(
                center.x + cameraDistance * 0.7,
                center.y + cameraDistance * 0.7,
                center.z + cameraDistance * 0.7
            )

            // 设置相机目标
            this.controls.target.copy(center)
            this.camera.lookAt(center)

            // 更新相机的near和far平面
            this.camera.near = cameraDistance / 100
            this.camera.far = cameraDistance * 10
            this.camera.updateProjectionMatrix()

            // 更新控制器约束
            this.controls.minDistance = cameraDistance * 0.1
            this.controls.maxDistance = cameraDistance * 5

            // 更新控制器
            this.controls.update()

            // 更新坐标轴大小和位置
            if (this.axesHelper) {
                const axesSize = maxDim * 0.3
                this.axesHelper.scale.setScalar(axesSize)
                this.axesHelper.position.copy(center)
            }
        },



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
            ]
            return colors[index % colors.length]
        },

        async loadGLTFModel() {
            try {
                this.isLoading = true
                this.clearCurrentModel()

                const loader = new GLTFLoader()
                const gltfPath = '/model_gltf/output_model.gltf'

                console.log('开始加载GLTF模型...')

                const gltf = await new Promise((resolve, reject) => {
                    loader.load(
                        gltfPath,
                        (gltf) => resolve(gltf),
                        (progress) => {
                            console.log('GLTF加载进度:', (progress.loaded / progress.total * 100).toFixed(2) + '%')
                        },
                        (error) => reject(error)
                    )
                })

                console.log('GLTF模型加载成功:', gltf)

                // 处理GLTF场景
                this.processGLTFScene(gltf)

                // 更新模型信息
                this.modelInfo.name = 'GLTF模型'
                this.modelInfo.totalVertices = this.calculateGLTFVertices(gltf.scene)
                this.modelInfo.totalTriangles = this.calculateGLTFTriangles(gltf.scene)
                this.updateModelInfo()

                // 调整相机视角 - 使用重新组织后的layerMeshes
                if (this.layerMeshes.length > 0) {
                    console.log(`加载了 ${this.layerMeshes.length} 个图层网格`)
                    this.fitCameraToModels(this.layerMeshes)
                } else {
                    console.warn('警告：没有找到可渲染的网格')
                }

                console.log('GLTF模型加载完成')

            } catch (error) {
                console.error('GLTF模型加载失败:', error)
                alert(`GLTF模型加载失败: ${error.message}`)
            } finally {
                this.isLoading = false
            }
        },

        processGLTFScene(gltf) {
            const scene = gltf.scene

            // 遍历场景中的所有网格
            const meshes = []
            scene.traverse((child) => {
                if (child.isMesh) {
                    meshes.push(child)
                }
            })

            console.log(`找到 ${meshes.length} 个网格对象`)

            if (meshes.length === 0) {
                console.warn('GLTF场景中没有找到任何网格对象')
                return
            }

            // 为每个网格创建图层
            meshes.forEach((mesh, index) => {
                const layerName = mesh.name || `GLTF图层 ${index + 1}`

                // 创建图层信息
                const layer = {
                    id: index + 1,
                    name: layerName,
                    visible: true,
                    opacity: 1,
                    color: this.generateLayerColor(index)
                }

                this.layers.push(layer)

                // 优化材质 - 使用MeshBasicMaterial避免阴影
                const originalMaterial = mesh.material
                const basicMaterial = new THREE.MeshBasicMaterial({
                    color: layer.color,
                    transparent: true,
                    opacity: layer.opacity,
                    side: THREE.DoubleSide
                })

                // 如果原材质有纹理，保留纹理
                if (originalMaterial && originalMaterial.map) {
                    basicMaterial.map = originalMaterial.map
                }

                mesh.material = basicMaterial

                // 创建边缘线
                const edges = new THREE.EdgesGeometry(mesh.geometry)
                const edgesMaterial = new THREE.LineBasicMaterial({
                    color: 0x000000,
                    transparent: true,
                    opacity: 0.8,
                    // 使用极小的深度偏移，避免几何偏移
                    polygonOffset: true,
                    polygonOffsetFactor: -0.01,
                    polygonOffsetUnits: -0.01
                })
                const edgeLines = new THREE.LineSegments(edges, edgesMaterial)
                // 设置渲染顺序确保边缘线在模型之后渲染
                edgeLines.renderOrder = 1
                mesh.renderOrder = 0
                edgeLines.visible = this.showEdges

                // 创建图层组
                const layerGroup = new THREE.Group()
                layerGroup.add(mesh)
                layerGroup.add(edgeLines)
                layerGroup.userData = {
                    layerId: layer.id,
                    mesh: mesh,
                    edges: edgeLines,
                    material: basicMaterial,
                    edgesMaterial: edgesMaterial
                }

                this.scene.add(layerGroup)
                this.layerMeshes.push(layerGroup)
            })

            console.log(`创建了 ${this.layers.length} 个图层`)
        },

        calculateGLTFVertices(scene) {
            let totalVertices = 0
            scene.traverse((child) => {
                if (child.isMesh && child.geometry) {
                    const positions = child.geometry.attributes.position
                    if (positions) {
                        totalVertices += positions.count
                    }
                }
            })
            return totalVertices
        },

        calculateGLTFTriangles(scene) {
            let totalTriangles = 0
            scene.traverse((child) => {
                if (child.isMesh && child.geometry) {
                    const geometry = child.geometry
                    if (geometry.index) {
                        totalTriangles += geometry.index.count / 3
                    } else if (geometry.attributes.position) {
                        totalTriangles += geometry.attributes.position.count / 3
                    }
                }
            })
            return Math.floor(totalTriangles)
        },

        clearCurrentModel() {
            // 清除当前模型
            this.layerMeshes.forEach(layerGroup => {
                this.scene.remove(layerGroup)
                // 清理几何体和材质
                if (layerGroup.userData.mesh) {
                    if (layerGroup.userData.mesh.geometry) layerGroup.userData.mesh.geometry.dispose()
                    if (layerGroup.userData.material) layerGroup.userData.material.dispose()
                }
                if (layerGroup.userData.edges) {
                    if (layerGroup.userData.edges.geometry) layerGroup.userData.edges.geometry.dispose()
                    if (layerGroup.userData.edgesMaterial) layerGroup.userData.edgesMaterial.dispose()
                }
            })
            this.layerMeshes = []
            this.layers = []
        },

        updateModelInfo() {
            let totalVertices = 0
            let totalFaces = 0

            this.layerMeshes.forEach(layerGroup => {
                if (layerGroup.userData.mesh && layerGroup.userData.mesh.geometry) {
                    const geometry = layerGroup.userData.mesh.geometry
                    totalVertices += geometry.attributes.position.count
                    if (geometry.index) {
                        totalFaces += geometry.index.count / 3
                    } else {
                        totalFaces += geometry.attributes.position.count / 3
                    }
                }
            })

            this.modelInfo.vertices = totalVertices
            this.modelInfo.faces = Math.floor(totalFaces)
        },

        toggleLayer(layer) {
            const layerGroup = this.layerMeshes.find(m => m.userData.layerId === layer.id)
            if (layerGroup) {
                layerGroup.visible = layer.visible
            }
        },

        updateLayerOpacity(layer) {
            const layerGroup = this.layerMeshes.find(m => m.userData.layerId === layer.id)
            if (layerGroup && layerGroup.userData.material) {
                const opacity = parseFloat(layer.opacity)
                layerGroup.userData.material.opacity = opacity
                // 同时更新边缘线的透明度
                if (layerGroup.userData.edgesMaterial) {
                    layerGroup.userData.edgesMaterial.opacity = Math.min(opacity + 0.2, 1.0)
                }
            }
        },

        toggleEdges() {
            this.showEdges = !this.showEdges
            this.layerMeshes.forEach(layerGroup => {
                if (layerGroup.userData.edges) {
                    layerGroup.userData.edges.visible = this.showEdges
                }
            })
        },

        toggleAxes() {
            this.showAxes = !this.showAxes
            if (this.axesHelper) {
                this.axesHelper.visible = this.showAxes
            }
        },

        setViewAngle(direction) {
            if (this.layerMeshes.length === 0) {
                // 如果没有模型，使用默认位置
                this.setDefaultViewAngle(direction)
                return
            }

            // 计算模型的边界框和中心
            const box = new THREE.Box3()
            this.layerMeshes.forEach(layerGroup => {
                if (layerGroup.userData.mesh) {
                    box.expandByObject(layerGroup.userData.mesh)
                }
            })

            if (box.isEmpty()) {
                this.setDefaultViewAngle(direction)
                return
            }

            const center = box.getCenter(new THREE.Vector3())
            const size = box.getSize(new THREE.Vector3())
            const maxDim = Math.max(size.x, size.y, size.z)
            const distance = maxDim * 2

            // 更新坐标轴大小以匹配模型
            if (this.axesHelper) {
                this.axesHelper.scale.setScalar(maxDim * 0.3)
                this.axesHelper.position.copy(center)
            }

            let cameraPosition = new THREE.Vector3()

            switch (direction) {
                case 'front':
                    cameraPosition.set(center.x, center.y, center.z + distance)
                    break
                case 'back':
                    cameraPosition.set(center.x, center.y, center.z - distance)
                    break
                case 'left':
                    cameraPosition.set(center.x - distance, center.y, center.z)
                    break
                case 'right':
                    cameraPosition.set(center.x + distance, center.y, center.z)
                    break
                case 'top':
                    cameraPosition.set(center.x, center.y + distance, center.z)
                    break
                case 'bottom':
                    cameraPosition.set(center.x, center.y - distance, center.z)
                    break
                case 'isometric':
                    cameraPosition.set(
                        center.x + distance * 0.7,
                        center.y + distance * 0.7,
                        center.z + distance * 0.7
                    )
                    break
                default:
                    cameraPosition.set(center.x + distance, center.y + distance, center.z + distance)
            }

            // 平滑动画到新位置
            this.animateCameraTo(cameraPosition, center)
        },

        setDefaultViewAngle(direction) {
            const distance = 20
            let cameraPosition = new THREE.Vector3()
            const center = new THREE.Vector3(0, 0, 0)

            switch (direction) {
                case 'front':
                    cameraPosition.set(0, 0, distance)
                    break
                case 'back':
                    cameraPosition.set(0, 0, -distance)
                    break
                case 'left':
                    cameraPosition.set(-distance, 0, 0)
                    break
                case 'right':
                    cameraPosition.set(distance, 0, 0)
                    break
                case 'top':
                    cameraPosition.set(0, distance, 0)
                    break
                case 'bottom':
                    cameraPosition.set(0, -distance, 0)
                    break
                case 'isometric':
                    cameraPosition.set(distance * 0.7, distance * 0.7, distance * 0.7)
                    break
                default:
                    cameraPosition.set(distance, distance, distance)
            }

            this.animateCameraTo(cameraPosition, center)
        },

        animateCameraTo(targetPosition, targetLookAt) {
            // 使用简单的动画到目标位置
            const startPosition = this.camera.position.clone()
            const startTarget = this.controls.target.clone()

            const duration = 1000 // 1秒动画
            const startTime = Date.now()

            const animate = () => {
                const elapsed = Date.now() - startTime
                const progress = Math.min(elapsed / duration, 1)

                // 使用easeInOutQuad缓动函数
                const easeProgress = progress < 0.5
                    ? 2 * progress * progress
                    : 1 - Math.pow(-2 * progress + 2, 2) / 2

                // 插值相机位置
                this.camera.position.lerpVectors(startPosition, targetPosition, easeProgress)
                this.controls.target.lerpVectors(startTarget, targetLookAt, easeProgress)

                this.camera.lookAt(this.controls.target)
                this.controls.update()

                if (progress < 1) {
                    requestAnimationFrame(animate)
                }
            }

            animate()
        },

        toggleInfo() {
            this.showInfo = !this.showInfo
        },

        resetView() {
            if (this.layerMeshes.length > 0) {
                this.fitCameraToModels(this.layerMeshes)
            } else {
                this.camera.position.set(10, 10, 10)
                this.controls.target.set(0, 0, 0)
                this.camera.lookAt(0, 0, 0)
                this.controls.update()
            }
        },

        toggleWireframe(wireframe) {
            this.layerMeshes.forEach(mesh => {
                mesh.material.wireframe = wireframe
            })
        },

        animate() {
            requestAnimationFrame(this.animate)
            this.controls.update()
            this.renderer.render(this.scene, this.camera)
        },

        onWindowResize() {
            const container = document.getElementById('three-container')
            if (container) {
                this.camera.aspect = container.clientWidth / container.clientHeight
                this.camera.updateProjectionMatrix()
                this.renderer.setSize(container.clientWidth, container.clientHeight)
            }
        }
    }
}
</script>

<style scoped>
.model-viewer {
    display: flex;
    height: 100%;
    background: #f5f5f5;
}

.viewer-container {
    flex: 1;
    position: relative;
}

.three-container {
    width: 100%;
    height: 100%;
    position: relative;
}

.info-panel {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(255, 255, 255, 0.9);
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    min-width: 200px;
}

.info-panel h3 {
    margin: 0 0 10px 0;
    color: #333;
    border-bottom: 1px solid #eee;
    padding-bottom: 5px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    margin: 8px 0;
    font-size: 14px;
}

.info-item label {
    font-weight: bold;
    color: #555;
}

.loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.loader {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 10px;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.control-panel {
    width: 280px;
    background: white;
    padding: 20px;
    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
    overflow-y: auto;
}

.panel-section {
    margin-bottom: 25px;
}

.panel-section h4 {
    margin: 0 0 15px 0;
    color: #333;
    border-bottom: 2px solid #667eea;
    padding-bottom: 5px;
}

.panel-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 4px;
    cursor: pointer;
    margin: 5px 5px 5px 0;
    transition: background-color 0.3s ease;
}

.panel-btn:hover {
    background: #5a6fd8;
}

.layer-item {
    display: flex;
    align-items: center;
    margin: 10px 0;
    padding: 8px;
    background: #f8f9fa;
    border-radius: 4px;
}

.layer-item input[type="checkbox"] {
    margin-right: 8px;
}

.layer-item label {
    flex: 1;
    font-size: 14px;
    color: #333;
}

.opacity-slider {
    width: 60px;
    margin-left: 10px;
}

.model-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.gltf-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.gltf-btn:hover {
    background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    transform: translateY(-1px);
}

.control-group {
    margin-bottom: 15px;
}

.control-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #333;
}

.view-controls {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
    margin-top: 10px;
}

.view-btn {
    padding: 8px 12px;
    border: 1px solid #ddd;
    background: #f8f9fa;
    cursor: pointer;
    border-radius: 4px;
    font-size: 12px;
    text-align: center;
    transition: all 0.2s ease;
}

.view-btn:hover {
    background: #e9ecef;
    border-color: #007bff;
    color: #007bff;
}

.view-btn:active {
    background: #007bff;
    color: white;
    transform: translateY(1px);
}
</style>
