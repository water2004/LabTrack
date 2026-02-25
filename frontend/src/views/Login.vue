<template>
  <div class="login-wrapper">
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    
    <el-card class="login-card" shadow="hover">
      <div class="login-header">
        <div class="logo-circle">
          <el-icon :size="40" color="#409EFF"><Stopwatch /></el-icon>
        </div>
        <h1>LabTrack</h1>
        <p>实验室资产与效率管理系统</p>
      </div>
      
      <div class="login-body">
        <el-input 
          v-model="username" 
          placeholder="请输入用户名" 
          :prefix-icon="User"
          size="large"
          class="custom-input"
          @keyup.enter="handleLogin" 
        />
        
        <el-button 
          type="primary" 
          size="large" 
          @click="handleLogin" 
          :loading="loading"
          class="submit-btn"
        >
          立即进入系统
        </el-button>
        
        <div class="login-footer">
          <span class="tip">还没有账号？</span>
          <el-link type="primary" :underline="false" @click="ElMessage.info('请联系管理员为您添加账号')">如何获取？</el-link>
          <div class="divider"></div>
          <el-link type="info" :underline="false" @click="$router.push('/admin-login')">管理后台入口</el-link>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { User, Stopwatch } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const username = ref('');
const loading = ref(false);
const router = useRouter();

const handleLogin = async () => {
  if (!username.value) return;
  loading.value = true;
  try {
    const res = await api.post('/auth/login', { username: username.value });
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('username', username.value);
    router.push('/');
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '登录失败，用户可能不存在');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
}
.shape-1 {
  top: -100px;
  left: -100px;
  width: 500px;
  height: 500px;
  background: rgba(64, 158, 255, 0.15);
}
.shape-2 {
  bottom: -150px;
  right: -150px;
  width: 600px;
  height: 600px;
  background: rgba(103, 194, 58, 0.1);
}

.login-card {
  width: 400px;
  border-radius: 16px;
  z-index: 1;
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}
.logo-circle {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}
.login-header h1 {
  margin: 0;
  font-size: 28px;
  color: #303133;
  letter-spacing: 1px;
}
.login-header p {
  margin: 5px 0 0;
  color: #909399;
  font-size: 14px;
}

.custom-input {
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  font-size: 16px;
  height: 44px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: transform 0.2s;
}
.submit-btn:active {
  transform: scale(0.98);
}

.login-footer {
  margin-top: 25px;
  text-align: center;
  font-size: 13px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #909399;
}
.divider {
  width: 1px;
  height: 12px;
  background: #dcdfe6;
  margin: 0 15px;
}
</style>
