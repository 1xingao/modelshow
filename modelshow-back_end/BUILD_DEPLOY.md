# ModelShow 构建和部署说明

## 快速开始

### 1. 开发环境运行
```bash
# 启动开发服务器
npm run serve
```

### 2. 构建生产版本
```bash
# 构建项目
npm run build

# 构建生产环境版本
npm run build:prod
```

### 3. 部署和测试

#### 使用内置测试服务器
```bash
# 安装 express 和 cors (如果还没安装)
npm install express cors

# 构建并启动测试服务器
npm run build
node deploy-server.js
```

然后访问 `http://localhost:3000` 查看应用。

#### 使用简单预览
```bash
# 使用 http-server 快速预览
npm run preview
```

## API 端点

构建后的应用会自动连接到以下 API 端点：

- `GET /api/model` - 获取默认3D模型
- `GET /api/models` - 获取可用模型列表  
- `GET /api/health` - 健康检查

## 配置说明

### 环境变量
- 开发环境：`.env.development`
- 生产环境：`.env.production`

主要配置项：
- `VUE_APP_API_BASE_URL` - API 基础地址

### 代理配置
开发环境下，`vue.config.js` 中配置了 `/api` 路径的代理，会自动转发到后端服务器。

## 文件结构

```
dist/                 # 构建输出目录
src/
  components/
    ModelViewer.vue   # 主要的3D模型查看器组件
  utils/
    api.js           # API工具类
public/
  model*/            # 模型文件目录
deploy-server.js     # 部署测试服务器
vue.config.js        # Vue CLI 配置
```

## 故障排除

### 1. 模型加载失败
- 检查 `/api/model` 端点是否正常响应
- 确认模型文件存在于 `public/model*` 目录中
- 查看浏览器控制台的错误信息

### 2. API 连接失败
- 确认后端服务器运行在正确端口 (默认3000)
- 检查 CORS 配置
- 验证环境变量 `VUE_APP_API_BASE_URL` 设置

### 3. 构建失败
- 确认所有依赖已正确安装: `npm install`
- 检查 Node.js 版本兼容性
- 清理缓存: `npm run clean` (如果有配置)

## 生产部署建议

1. **静态文件服务**: 将 `dist` 目录部署到 Web 服务器
2. **API 服务**: 确保后端 API 服务正常运行
3. **HTTPS**: 生产环境建议使用 HTTPS
4. **CDN**: 可考虑使用 CDN 加速静态资源

## 性能优化

- 构建时会自动进行代码分割
- 模型文件建议压缩和优化
- 启用 gzip 压缩
- 考虑使用 Web Workers 处理大型模型