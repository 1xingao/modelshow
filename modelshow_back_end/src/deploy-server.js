const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const os = require('os');

const app = express();
const PORT = 3000;

// 获取本机局域网IP地址
function getLocalIPAddress() {
    const interfaces = os.networkInterfaces();
    for (const interfaceName in interfaces) {
        const addresses = interfaces[interfaceName];
        for (const addressInfo of addresses) {
            // 查找IPv4且不是回环地址的网络接口
            if (addressInfo.family === 'IPv4' && !addressInfo.internal) {
                return addressInfo.address;
            }
        }
    }
    return 'localhost';
}

// 启用 CORS
app.use(cors());

// 解析 JSON 和 URL 编码的请求体
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 静态文件服务 - 服务构建后的 Vue 应用
app.use(express.static(path.join(__dirname, 'dist')));

// API 路由 - 健康检查
app.get('/api/health', (req, res) => {
    console.log('健康检查请求');
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        server: 'ModelShow API Server'
    });
});

// API 路由 - 模型文件服务
app.get('/api/model', (req, res) => {
    console.log('收到模型请求 - 优先使用 model_gltf 目录');
    
    // 首先专门查找 model_gltf 目录中的文件
    const modelGltfDir = path.join(__dirname, 'public', 'model_gltf');
    let modelPath = null;
    
    if (fs.existsSync(modelGltfDir)) {
        try {
            const files = fs.readdirSync(modelGltfDir);
            console.log('model_gltf 目录中的文件:', files);
            
            // 优先选择 GLB 文件（自包含格式，无需额外依赖）
            let modelFile = files.find(file => file.endsWith('.glb'));
            if (!modelFile) {
                // 如果没有GLB文件，选择GLTF文件
                modelFile = files.find(file => file.endsWith('.gltf'));
            }
            
            if (modelFile) {
                modelPath = path.join(modelGltfDir, modelFile);
                console.log('在 model_gltf 目录找到模型:', modelFile);
            }
        } catch (err) {
            console.warn(`无法读取 model_gltf 目录:`, err.message);
        }
    }
    
    // 如果 model_gltf 中没有找到文件，再查找其他目录
    if (!modelPath) {
        console.log('model_gltf 目录中未找到模型，搜索其他目录...');
        const fallbackPaths = [
            path.join(__dirname, 'public', 'model_3dtiles', 'output_model', 'coal3-1_7.gltf'),
            path.join(__dirname, 'public', 'model_gltf_test', '2CylinderEngine.gltf'),
        ];

        for (const searchPath of fallbackPaths) {
            if (fs.existsSync(searchPath)) {
                modelPath = searchPath;
                console.log('在备用路径找到模型:', searchPath);
                break;
            }
        }
    }
    
    console.log('找到模型文件:', modelPath);
    
    if (modelPath && fs.existsSync(modelPath)) {
        try {
            const stat = fs.statSync(modelPath);
            const fileExtension = path.extname(modelPath).toLowerCase();
            
            if (fileExtension === '.gltf') {
                // 对于 GLTF 文件，修改 URI 路径以指向正确的服务器路径

                const gltfContent = fs.readFileSync(modelPath, 'utf8');
                const gltfData = JSON.parse(gltfContent);
                
                // 修改 buffers 中的 URI，使其指向服务器的正确路径
                if (gltfData.buffers) {
                    gltfData.buffers.forEach(buffer => {
                        if (buffer.uri && buffer.uri.endsWith('.bin')) {
                            // 将相对路径改为绝对路径
                            buffer.uri = `/model_gltf/${buffer.uri}`
                        }
                    });
                }
                
                const modifiedContent = JSON.stringify(gltfData);
                
                res.setHeader('Content-Type', 'model/gltf+json');
                res.setHeader('Content-Length', Buffer.byteLength(modifiedContent));
                res.setHeader('Access-Control-Allow-Origin', '*');
                
                console.log(`发送修正后的 GLTF 文件: ${path.basename(modelPath)} (${modifiedContent.length} chars)`);
                res.send(modifiedContent);
            } else {
                // 对于 GLB 文件，直接发送
                res.setHeader('Content-Type', 'model/gltf-binary');
                res.setHeader('Content-Length', stat.size);
                res.setHeader('Access-Control-Allow-Origin', '*');
                
                console.log(`发送 GLB 文件: ${path.basename(modelPath)} (${stat.size} bytes)`);
                res.sendFile(modelPath);
            }
            
        } catch (err) {
            console.error('读取模型文件时出错:', err);
            res.status(500).json({ 
                error: '读取模型文件失败',
                message: err.message
            });
        }
    } else {
        console.error('未找到模型文件');
        res.status(404).json({ 
            error: '模型文件不存在',
            message: '请确保在以下目录中至少有一个 .gltf 或 .glb 文件',
            searchedPaths: [
                'public/model_gltf_test/',
                'public/model_gltf/',
                'public/model_3dtiles/output_model/'
            ]
        });
    }
});

// 专门处理 GLTF 缓冲区文件（.bin 文件）
app.get('/gltf_buffer_:id.bin', (req, res) => {
    const bufferId = req.params.id;
    const fileName = `gltf_buffer_${bufferId}.bin`;
    
    // 搜索所有可能的目录
    const searchDirs = [
        path.join(__dirname, 'public', 'model_gltf'),
        path.join(__dirname, 'public', 'model_3dtiles', 'output_model'),
        path.join(__dirname, 'public', 'model_gltf_test')
    ];
    
    for (const dir of searchDirs) {
        const filePath = path.join(dir, fileName);
        if (fs.existsSync(filePath)) {
            console.log(`发送缓冲区文件: ${fileName} 从 ${dir}`);
            res.setHeader('Content-Type', 'application/octet-stream');
            res.setHeader('Access-Control-Allow-Origin', '*');
            return res.sendFile(filePath);
        }
    }
    
    console.error(`未找到缓冲区文件: ${fileName}`);
    res.status(404).json({ error: `缓冲区文件不存在: ${fileName}` });
});

// 记录所有请求以便调试
app.use((req, res, next) => {
    console.log(`📥 ${req.method} ${req.path} - ${req.get('User-Agent')?.includes('Mozilla') ? 'Browser' : 'Other'}`);
    next();
});

// 使用中间件处理 .bin 文件请求
app.use((req, res, next) => {
    // 检查是否是 .bin 文件请求
    if (req.path.endsWith('.bin') || req.path.includes('gltf_buffer_')) {
        const fileName = path.basename(req.path);
        console.log(`🔍 请求二进制文件: ${req.path} -> ${fileName}`);
        
        // 优先从 model_gltf 目录查找
        const searchDirs = [
            path.join(__dirname, 'public', 'model_gltf'),
            path.join(__dirname, 'public', 'model_3dtiles', 'output_model'),
            path.join(__dirname, 'public', 'model_gltf_test')
        ];
        
        for (const dir of searchDirs) {
            const filePath = path.join(dir, fileName);
            console.log(`   🔎 检查: ${filePath} - ${fs.existsSync(filePath) ? '存在' : '不存在'}`);
            if (fs.existsSync(filePath)) {
                const stat = fs.statSync(filePath);
                console.log(`✅ 发送二进制文件: ${fileName} (${stat.size} bytes) 从 ${path.relative(__dirname, dir)}`);
                res.setHeader('Content-Type', 'application/octet-stream');
                res.setHeader('Content-Length', stat.size);
                res.setHeader('Access-Control-Allow-Origin', '*');
                res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
                res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Range');
                res.setHeader('Cache-Control', 'public, max-age=31536000'); // 缓存1年
                return res.sendFile(filePath);
            }
        }
        
        console.error(`❌ 未找到二进制文件: ${fileName} (请求路径: ${req.path})`);
        console.log(`   搜索的目录:`, searchDirs.map(dir => path.relative(__dirname, dir)));
        return res.status(404).json({ 
            error: `二进制文件不存在: ${fileName}`,
            requestPath: req.path,
            searchedDirs: searchDirs.map(dir => path.relative(__dirname, dir))
        });
    }
    
    next();
});

// 为模型相关的静态资源提供服务
app.use('/public', express.static(path.join(__dirname, 'public'), {
    setHeaders: (res, filePath) => {
        if (filePath.endsWith('.bin')) {
            res.setHeader('Content-Type', 'application/octet-stream');
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Range');
        }
    }
}));

// 直接提供 model_gltf 目录的静态文件访问（作为备用）
app.use('/model_gltf', express.static(path.join(__dirname, 'public', 'model_gltf'), {
    setHeaders: (res, filePath) => {
        if (filePath.endsWith('.bin')) {
            console.log(`📤 通过静态服务提供: ${path.basename(filePath)}`);
            res.setHeader('Content-Type', 'application/octet-stream');
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Range');
        }
    }
}));

// API 路由 - 获取可用模型列表
app.get('/api/models', (req, res) => {
    console.log('获取模型列表请求');
    const models = [];
    
    // 检查各个目录中的模型文件
    const directories = [
        { path: path.join(__dirname, 'public', 'model_gltf'), type: 'gltf' },
        { path: path.join(__dirname, 'public', 'model_3dtiles', 'output_model'), type: '3dtiles' },
        { path: path.join(__dirname, 'public', 'model_gltf_test'), type: 'test' }
    ];
    
    directories.forEach(dir => {
        if (fs.existsSync(dir.path)) {
            try {
                const files = fs.readdirSync(dir.path);
                files.forEach(file => {
                    if (file.endsWith('.gltf') || file.endsWith('.glb')) {
                        const filePath = path.join(dir.path, file);
                        const stat = fs.statSync(filePath);
                        models.push({
                            name: file,
                            type: dir.type,
                            size: stat.size,
                            path: `/api/model`,
                            lastModified: stat.mtime
                        });
                    }
                });
            } catch (err) {
                console.warn(`无法读取目录 ${dir.path}:`, err.message);
            }
        }
    });
    
    res.json({ models, count: models.length });
});

// 处理其他 API 路由（404） - 使用正则表达式
app.use(/^\/api\//, (req, res) => {
    res.status(404).json({ 
        error: 'API 端点不存在',
        path: req.path,
        availableEndpoints: ['/api/health', '/api/model', '/api/models']
    });
});

// SPA 回退路由 - 使用 app.use 而不是 app.get('*')
app.use((req, res) => {
    const indexPath = path.join(__dirname, 'dist', 'index.html');
    if (fs.existsSync(indexPath)) {
        res.sendFile(indexPath);
    } else {
        res.status(404).send(`
            <h1>应用尚未构建</h1>
            <p>请先运行 <code>npm run build</code> 构建前端应用</p>
            <p>然后重新启动服务器</p>
        `);
    }
});

// 启动服务器 - 监听所有网络接口
app.listen(PORT, '0.0.0.0', () => {
    const localIP = getLocalIPAddress();
    console.log('='.repeat(60));
    console.log(`🚀 ModelShow 服务器已启动`);
    console.log(`🌐 本地访问: http://localhost:${PORT}`);
    console.log(`🌐 局域网访问: http://${localIP}:${PORT}`);
    console.log(`📊 模型API: http://${localIP}:${PORT}/api/model`);
    console.log(`🏥 健康检查: http://${localIP}:${PORT}/api/health`);
    console.log(`📁 模型列表: http://${localIP}:${PORT}/api/models`);
    console.log('='.repeat(60));
    
    // 检查构建文件是否存在
    const distIndex = path.join(__dirname, 'dist', 'index.html');
    if (!fs.existsSync(distIndex)) {
        console.log('⚠️  注意: 请先运行 npm run build 构建前端应用');
    }
    
    // 检查模型文件
    const modelGltfDir = path.join(__dirname, 'public', 'model_gltf');
    
    if (fs.existsSync(modelGltfDir)) {
        try {
            const files = fs.readdirSync(modelGltfDir);
            const modelFiles = files.filter(f => f.endsWith('.gltf') || f.endsWith('.glb'));
            const binFiles = files.filter(f => f.endsWith('.bin'));
            
            if (modelFiles.length > 0) {
                console.log(`📦 主要模型目录 model_gltf:`);
                console.log(`   - 模型文件: ${modelFiles.join(', ')}`);
                console.log(`   - 缓冲区文件: ${binFiles.length} 个 .bin 文件`);
                console.log(`✅ /api/model 将返回: ${modelFiles[0]}`);
            }
        } catch (err) {
            console.error('读取 model_gltf 目录出错:', err.message);
        }
    } else {
        console.log('⚠️  警告: model_gltf 目录不存在');
    }
    
    // 检查其他目录作为备用
    const otherDirs = [
        path.join(__dirname, 'public', 'model_3dtiles', 'output_model'),
        path.join(__dirname, 'public', 'model_gltf_test')
    ];
    
    otherDirs.forEach(dir => {
        if (fs.existsSync(dir)) {
            try {
                const files = fs.readdirSync(dir);
                const modelFiles = files.filter(f => f.endsWith('.gltf') || f.endsWith('.glb'));
                if (modelFiles.length > 0) {
                    console.log(`� 备用目录 ${path.relative(__dirname, dir)}: ${modelFiles.length} 个模型文件`);
                }
            } catch (err) {
                // 忽略读取错误
            }
        }
    });
    
    console.log('='.repeat(50));
});