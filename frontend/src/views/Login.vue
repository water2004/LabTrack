<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>LabTrack 登录</h2>
      <el-input v-model="username" placeholder="请输入用户名 (如: ZhangSan)" @keyup.enter="handleLogin" />
      <el-button type="primary" @click="handleLogin" style="width: 100%; margin-top: 20px;">进入系统</el-button>
      <div style="margin-top: 20px; text-align: center;">
        <el-link type="info" @click="$router.push('/admin-login')">管理后台</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { ElMessage } from 'element-plus';

const username = ref('');
const router = useRouter();

const handleLogin = async () => {
  if (!username.value) return;
  try {
    const res = await api.post('/auth/login', { username: username.value });
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('username', username.value);
    router.push('/');
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '登录失败');
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
