<template>
  <div class="login-wrapper">
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    
    <el-card class="login-card" shadow="hover">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="28" color="#fff"><Setting /></el-icon>
        </div>
        <h2>管理后台登录</h2>
        <p>LabTrack 资产管理系统</p>
      </div>

      <el-form @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input 
            v-model="password" 
            type="password" 
            placeholder="请输入管理密码" 
            size="large"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-button 
          type="primary" 
          size="large" 
          class="login-btn" 
          @click="handleLogin"
          :loading="loading"
        >
          立即进入控制面板
        </el-button>
      </el-form>

      <div class="login-footer">
        <el-link type="info" underline="never" @click="$router.push('/login')">
          <el-icon><Back /></el-icon> 返回用户登录
        </el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { Setting, Lock, Back } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const password = ref('');
const loading = ref(false);
const router = useRouter();

const handleLogin = async () => {
  if (!password.value) return ElMessage.warning('请输入管理密码');
  loading.value = true;
  try {
    const res = await api.post('/admin/auth', { password: password.value });
    localStorage.setItem('isAdmin', 'true');
    localStorage.setItem('token', res.data.access_token);
    ElMessage.success('欢迎回来，管理员');
    router.push('/admin');
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '密码验证失败');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  width: 100vw;
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
  filter: blur(80px);
  z-index: 0;
  border-radius: 50%;
}
.shape-1 {
  width: 400px;
  height: 400px;
  background: rgba(64, 158, 255, 0.15);
  top: -100px;
  right: -100px;
}
.shape-2 {
  width: 300px;
  height: 300px;
  background: rgba(103, 194, 58, 0.1);
  bottom: -50px;
  left: -50px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 20px;
  border: none;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  padding: 20px;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}
.logo-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #606266 0%, #303133 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.login-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
  font-weight: 700;
}
.login-header p {
  color: #909399;
  margin-top: 8px;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}
.login-btn {
  width: 100%;
  border-radius: 12px;
  height: 48px;
  font-weight: 600;
  margin-top: 10px;
  background: #303133;
  border-color: #303133;
}
.login-btn:hover {
  background: #4b4d50;
  border-color: #4b4d50;
}

.login-footer {
  margin-top: 25px;
  text-align: center;
}
</style>
