// src/utils/api.js
import axios from 'axios';

// 调试环境变量
console.log('环境变量检查:');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('VUE_APP_API_BASE_URL:', process.env.VUE_APP_API_BASE_URL);

// 创建 axios 实例
const apiClient = axios.create({
    // 完全强制使用本地地址，忽略所有环境变量
    baseURL: 'http://localhost:3000',
    timeout: 30000, // 30秒超时
    headers: {
        'Content-Type': 'application/json',
    }
});

// 再次确保baseURL是正确的
apiClient.defaults.baseURL = 'http://localhost:3000';

console.log('API客户端配置:');
console.log('baseURL:', apiClient.defaults.baseURL);
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
    }
};

// 导出便捷函数
export const uploadStratumData = stratumAPI.uploadData;
export const getStratumFiles = stratumAPI.getFileList;

// 导出默认的 axios 实例
export default apiClient;