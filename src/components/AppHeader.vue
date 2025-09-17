<template>
  <header class="app-header">
    <div class="header-content">
      <div class="logo">
        <h1>三维地质模型可视化系统</h1>
      </div>
      <nav class="navigation">
        <ul class="nav-menu">
          <li class="nav-item">
            <a 
              href="#" 
              :class="{ 'active': activeTab === 'model' }" 
              @click="switchTab('model')"
            >
              模型可视化
            </a>
          </li>
          <li class="nav-item">
            <a 
              href="#" 
              :class="{ 'active': activeTab === 'upload' }" 
              @click="switchTab('upload')"
            >
              数据上传
            </a>
          </li>
          <li class="nav-item">
            <a 
              href="#" 
              :class="{ 'active': activeTab === 'process' }" 
              @click="switchTab('process')"
            >
              数据处理
            </a>
          </li>
          <li class="nav-item">
            <a 
              href="#" 
              :class="{ 'active': activeTab === 'settings' }" 
              @click="switchTab('settings')"
            >
              系统设置
            </a>
          </li>
        </ul>
      </nav>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppHeader',
  props: {
    activeTab: {
      type: String,
      default: 'model'
    }
  },
  methods: {
    /**
     * 切换页面标签
     * @param {string} tabName - 要切换到的标签名称
     */
    switchTab(tabName) {
      this.$emit('tab-changed', tabName);
    }
  }
}
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 60px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.navigation {
  height: 100%;
}

.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  height: 100%;
}

.nav-item {
  height: 100%;
  display: flex;
  align-items: center;
}

.nav-item a {
  color: white;
  text-decoration: none;
  padding: 0 20px;
  height: 100%;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
}

.nav-item a:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-bottom-color: rgba(255, 255, 255, 0.5);
}

.nav-item a.active {
  background-color: rgba(255, 255, 255, 0.15);
  border-bottom-color: white;
  font-weight: 600;
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 15px;
  }
  
  .logo h1 {
    font-size: 16px;
  }
  
  .nav-item a {
    padding: 0 15px;
    font-size: 14px;
  }
}
</style>