<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>管理后台登录</h2>
      <el-input v-model="password" type="password" placeholder="请输入管理密码" @keyup.enter="handleLogin" show-password />
      <el-button type="primary" @click="handleLogin" style="width: 100%; margin-top: 20px;">验证</el-button>
      <div style="margin-top: 20px; text-align: center;">
        <el-link type="info" @click="$router.push('/login')">返回用户登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { ElMessage } from 'element-plus';

const password = ref('');
const router = useRouter();

const handleLogin = async () => {
  if (!password.value) return;
  try {
    const res = await api.post('/admin/auth', { password: password.value });
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('isAdmin', 'true');
    router.push('/admin');
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '密码错误');
  }
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}
.login-card {
  width: 350px;
}
</style>
