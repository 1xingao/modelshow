// src/utils/api.js
import axios from 'axios';

// 调试环境变量
console.log('环境变量检查:');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('VUE_APP_API_BASE_URL:', process.env.VUE_APP_API_BASE_URL);

// 动态获取API基础URL
function getApiBaseUrl() {
    // 如果是开发环境且在localhost，使用localhost
    if (process.env.NODE_ENV === 'development' && window.location.hostname === 'localhost') {
        return 'http://localhost:3000';
    }
    
    // 其他情况使用当前页面的主机名（支持局域网访问）
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:3000`;
}

// 创建 axios 实例
const apiClient = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000, // 30秒超时
    headers: {
        'Content-Type': 'application/json',
    }
});

console.log('API客户端配置:');
console.log('当前页面hostname:', window.location.hostname);
console.log('当前页面protocol:', window.location.protocol);
console.log('计算出的baseURL:', apiClient.defaults.baseURL);
console.log('完整URL示例:', apiClient.defaults.baseURL + '/api/model');

// 请求拦截器
apiClient.interceptors.request.use(
    (config) => {
        console.log('发送API请求:', config.method?.toUpperCase(), config.url);
        return config;
    },
    (error) => {
        console.error('请求配置错误:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
apiClient.interceptors.response.use(
    (response) => {
        console.log('API响应成功:', response.status, response.config.url);
        return response;
    },
    (error) => {
        console.error('API请求失败:', error.response?.status, error.config?.url, error.message);
        return Promise.reject(error);
    }
);

// 模型相关 API
export const modelAPI = {
    // 获取默认模型
    async getModel(path = '/api/model') {
        try {
            const response = await apiClient.get(path, {
                headers: {
                    'Accept': 'application/octet-stream, */*'
                },
                responseType: 'blob',
                onDownloadProgress: (progressEvent) => {
                    if (progressEvent.lengthComputable) {
                        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        console.log(`下载进度: ${percent}%`);
                        
                        // 可以触发事件让 UI 组件监听进度
                        if (window.modelLoadProgress) {
                            window.modelLoadProgress(percent);
                        }
                    }
                }
            });
            return response;
        } catch (error) {
            console.error('API错误详情:', error.response || error);
            throw new Error(`获取模型失败: ${error.message}`);
        }
    },

    // 检查 API 连接状态
    async checkConnection() {
        try {
            const response = await apiClient.get('/api/health', { timeout: 5000 });
            return response.status === 200;
        } catch (error) {
            console.warn('API连接检查失败:', error.message);
            return false;
        }
    },

    // 生成地质模型
    async generateGeological(data) {
        try {
            const response = await apiClient.post('/api/model/generate', data);
            return response.data;
        } catch (error) {
            console.error('生成地质模型失败:', error.response || error);
            throw new Error(`生成模型失败: ${error.response?.data?.message || error.message}`);
        }
    }
};

// 地层坐标数据相关 API
export const stratumAPI = {
    // 上传地层坐标数据文件
    async uploadData(formData, onProgress) {
        try {
            const response = await apiClient.post('/api/stratum/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                timeout: 60000, // 60秒超时
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.lengthComputable && onProgress) {
                        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        onProgress(percent);
                    }
                }
            });
            return response.data;
        } catch (error) {
            console.error('文件上传失败:', error.response || error);
            throw new Error(`上传失败: ${error.response?.data?.message || error.message}`);
        }
    },

    // 获取上传的文件列表
    async getFileList() {
        try {
            const response = await apiClient.get('/api/stratum/files');
            return response.data;
        } catch (error) {
            console.error('获取文件列表失败:', error.response || error);
            throw new Error(`获取文件列表失败: ${error.message}`);
        }
    },

    // 获取地层坐标数据内容
    async getData(filename) {
        try {
            const response = await apiClient.get(`/api/stratum/data/${encodeURIComponent(filename)}`);
            return response.data;
        } catch (error) {
            console.error('获取地层数据失败:', error.response || error);
            throw new Error(`获取数据失败: ${error.response?.data?.message || error.message}`);
        }
    }
};

// 导出便捷函数
export const uploadStratumData = stratumAPI.uploadData;
export const getStratumFiles = stratumAPI.getFileList;
export const getStratumData = stratumAPI.getData;
export const generateGeologicalModel = modelAPI.generateGeological;

// 导出默认的 axios 实例
export default apiClient;