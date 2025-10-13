import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

// 创建全局事件总线
Vue.prototype.$eventBus = new Vue()

new Vue({
  render: h => h(App),
}).$mount('#app')
