<template>
  <div class="admin-container">
    <el-container class="admin-layout">
      <!-- 侧边栏 -->
      <el-aside width="240px" class="admin-aside">
        <div class="logo-area">
          <el-icon :size="24" color="#fff"><Setting /></el-icon>
          <span>管理控制台</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="admin-menu"
          @select="handleMenuSelect"
          background-color="#1f2937"
          text-color="#9ca3af"
          active-text-color="#fff"
        >
          <el-menu-item index="overview">
            <el-icon><DataBoard /></el-icon>
            <span>概览统计</span>
          </el-menu-item>
          <el-menu-item index="users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="devices">
            <el-icon><Box /></el-icon>
            <span>资产列表</span>
          </el-menu-item>
          <el-menu-item index="records">
            <el-icon><Document /></el-icon>
            <span>使用记录</span>
          </el-menu-item>
          <el-menu-item index="settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>

        <div class="aside-footer">
          <el-button link type="info" @click="logout">
            <el-icon><SwitchButton /></el-icon> 退出系统
          </el-button>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="admin-main">
        <header class="main-header">
          <h2>{{ menuTitle }}</h2>
          <div class="header-right">
             <el-button link type="primary" @click="$router.push('/login')">返回主站</el-button>
          </div>
        </header>

        <div class="content-body">
          <!-- 概览面板 -->
          <div v-if="activeMenu === 'overview'" class="overview-section">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card shadow="never" class="stat-card">
                  <template #header>总设备数</template>
                  <div class="stat-value">{{ devices.length }}</div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="never" class="stat-card">
                  <template #header>活跃用户</template>
                  <div class="stat-value">{{ users.length }}</div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="never" class="stat-card">
                  <template #header>累计记录</template>
                  <div class="stat-value">{{ records.length }}</div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 用户管理 -->
          <div v-if="activeMenu === 'users'" class="card-section">
            <div class="table-actions">
              <el-input v-model="newUser" placeholder="输入新用户名" style="width: 250px" size="large">
                <template #append>
                  <el-button @click="addUser" type="primary">添加用户</el-button>
                </template>
              </el-input>
            </div>
            <el-table :data="users" stripe style="width: 100%">
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="username" label="用户名" />
            </el-table>
          </div>

          <!-- 资产列表 -->
          <div v-if="activeMenu === 'devices'" class="card-section">
            <div class="table-actions">
              <el-button type="success" @click="($refs.csvInput as any).click()">
                <el-icon><Upload /></el-icon> 批量导入 CSV
              </el-button>
              <input
                type="file"
                ref="csvInput"
                hidden
                accept=".csv"
                @change="handleCsvUpload"
              />
            </div>
            <el-table :data="devices" stripe style="width: 100%">
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="name" label="名称" width="150" show-overflow-tooltip />
              <el-table-column prop="asset_code" label="资产编号" width="120" />
              <el-table-column prop="manager" label="当前负责人" width="120" />
              <el-table-column label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="statusTag(scope.row.status)">
                    {{ statusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" min-width="180">
                <template #default="scope">
                  <el-button link type="primary" @click="viewQR(scope.row.id)">二维码</el-button>
                  <el-popconfirm 
                    title="确定删除该设备吗？不可恢复" 
                    confirm-button-text="确定"
                    cancel-button-text="取消"
                    @confirm="deleteDevice(scope.row.id)"
                  >
                    <template #reference>
                      <el-button link type="danger">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 使用记录 -->
          <div v-if="activeMenu === 'records'" class="card-section">
            <div class="table-actions">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                size="large"
              />
              <el-button type="success" @click="exportExcel" size="large">导出 Excel</el-button>
            </div>
            <el-table :data="records" stripe style="width: 100%" height="calc(100vh - 280px)">
              <el-table-column prop="device_name" label="设备" width="150" show-overflow-tooltip />
              <el-table-column prop="user_name" label="使用者" width="100" />
              <el-table-column prop="start_time" label="开始时间" width="160">
                <template #default="scope">{{ formatTime(scope.row.start_time) }}</template>
              </el-table-column>
              <el-table-column prop="end_time" label="结束时间" width="160">
                <template #default="scope">{{ formatTime(scope.row.end_time) }}</template>
              </el-table-column>
              <el-table-column prop="duration" label="时长(秒)" width="100" />
              <el-table-column prop="notes" label="备注" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- 系统设置 -->
          <div v-if="activeMenu === 'settings'" class="card-section">
            <el-form :model="config" label-width="160px" label-position="top" style="max-width: 600px;">
              <el-divider content-position="left">AI 视觉识别</el-divider>
              <p class="settings-hint">
                开启后，前台录入设备时可使用视觉模型按照片识别设备名称，并在扫码弹窗中按编号数字识别资产编号。
                需配置 OpenAI 兼容（Chat Completions）的视觉模型端点。
              </p>

              <el-form-item label="启用 AI 视觉识别">
                <el-switch v-model="config.vision_enabled" />
              </el-form-item>

              <template v-if="config.vision_enabled">
                <el-form-item label="端点 URL (OpenAI API)">
                  <el-input
                    v-model="config.vision_api_url"
                    placeholder="如: https://api.openai.com/v1"
                  />
                  <span class="settings-tip">填写到 /v1 即可，系统会自动追加 /chat/completions。</span>
                </el-form-item>
                <el-form-item label="模型名称">
                  <el-input v-model="config.vision_model" placeholder="如: gpt-4o-mini" />
                </el-form-item>
                <el-form-item label="API Key">
                  <el-input
                    v-model="config.vision_api_key"
                    type="password"
                    show-password
                    :placeholder="config.vision_api_key_set ? '已设置（留空则保持不变）' : '请输入 API Key'"
                  />
                </el-form-item>
              </template>

              <el-form-item>
                <el-button type="primary" @click="saveConfig" :loading="savingConfig">保存设置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-main>
    </el-container>

    <!-- CSV 导入结果弹窗 -->
    <el-dialog v-model="showCsvResult" title="CSV 导入结果" width="420px" center>
      <div style="line-height: 2;">
        <p><el-tag type="success">成功导入</el-tag> <strong>{{ csvResult.created }}</strong> 条</p>
        <p><el-tag type="warning">编号重复跳过</el-tag> <strong>{{ csvResult.skipped_duplicate }}</strong> 条</p>
        <p><el-tag type="info">编号为空跳过</el-tag> <strong>{{ csvResult.skipped_empty_code }}</strong> 条</p>
        <div v-if="csvResult.errors.length">
          <el-divider />
          <p style="color: #F56C6C; font-weight: 600;">错误详情：</p>
          <p v-for="(e, i) in csvResult.errors" :key="i" style="font-size: 13px; color: #909399;">{{ e }}</p>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showCsvResult = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api, { baseURL } from '../api';
import { ElMessage } from 'element-plus';
import {
  Setting, User, Box, Document, DataBoard,
  SwitchButton, Upload
} from '@element-plus/icons-vue';

const router = useRouter();
const activeMenu = ref('overview');
const users = ref<any[]>([]);
const devices = ref<any[]>([]);
const records = ref<any[]>([]);
const newUser = ref('');
const dateRange = ref([]);
const csvImporting = ref(false);
const showCsvResult = ref(false);
const csvResult = ref({ created: 0, skipped_duplicate: 0, skipped_empty_code: 0, errors: [] as string[] });

const config = ref({
  vision_enabled: false,
  vision_api_url: '',
  vision_model: '',
  vision_api_key: '',
  vision_api_key_set: false,
});
const savingConfig = ref(false);

const menuTitle = computed(() => {
  const titles: Record<string, string> = {
    overview: '概览统计',
    users: '用户管理',
    devices: '资产设备管理',
    records: '设备使用流水',
    settings: '系统设置'
  };
  return titles[activeMenu.value];
});

const handleMenuSelect = (index: string) => {
  activeMenu.value = index;
  if (index === 'users') fetchUsers();
  if (index === 'devices') fetchDevices();
  if (index === 'records') fetchRecords();
  if (index === 'settings') fetchConfig();
};

const fetchUsers = async () => {
  const res = await api.get('/admin/users');
  users.value = res.data;
};

const fetchDevices = async () => {
  const res = await api.get('/devices');
  devices.value = res.data;
};

const fetchRecords = async () => {
  const res = await api.get('/admin/records');
  records.value = res.data;
};

const fetchConfig = async () => {
  try {
    const res = await api.get('/admin/config');
    config.value = { ...res.data, vision_api_key: '' };
  } catch (err) {
    ElMessage.error('读取配置失败');
  }
};

const saveConfig = async () => {
  savingConfig.value = true;
  try {
    await api.post('/admin/config', {
      vision_enabled: config.value.vision_enabled,
      vision_api_url: config.value.vision_api_url,
      vision_model: config.value.vision_model,
      vision_api_key: config.value.vision_api_key || null,
    });
    ElMessage.success('设置已保存');
    fetchConfig();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '保存失败');
  } finally {
    savingConfig.value = false;
  }
};

const addUser = async () => {
  if (!newUser.value) return;
  try {
    await api.post('/admin/users', { username: newUser.value });
    ElMessage.success('用户添加成功');
    newUser.value = '';
    fetchUsers();
  } catch (err) {
    ElMessage.error('添加失败');
  }
};

const deleteDevice = async (id: number) => {
  try {
    await api.delete(`/admin/devices/${id}`);
    ElMessage.success('设备已删除');
    fetchDevices();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '删除失败');
  }
};

const handleCsvUpload = async (event: any) => {
  const file = event.target.files[0];
  if (!file) return;
  csvImporting.value = true;
  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/admin/import-csv', formData);
    csvResult.value = res.data;
    showCsvResult.value = true;
    fetchDevices();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '导入失败');
  } finally {
    csvImporting.value = false;
    event.target.value = '';
  }
};

const viewQR = (id: number) => {
  const url = `${window.location.origin}/?id=${id}`;
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(url)}`;
  window.open(qrUrl, '_blank');
};

const exportExcel = () => {
  let url = `${baseURL}/admin/export`;
  if (dateRange.value && dateRange.value.length === 2) {
    url += `?start_date=${dateRange.value[0]}&end_date=${dateRange.value[1]}`;
  }
  window.open(url, '_blank');
};

const logout = () => {
  localStorage.removeItem('isAdmin');
  router.push('/admin-login');
};

const statusText = (status: number) => {
  const texts = ['闲置', '使用中', '借出中', '故障'];
  return texts[status];
};

const statusTag = (status: number) => {
  const tags = ['success', 'danger', 'warning', 'info'];
  return tags[status];
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-';
  return new Date(timeStr).toLocaleString();
};

onMounted(() => {
  if (localStorage.getItem('isAdmin') !== 'true') {
    router.push('/admin-login');
    return;
  }
  // 初始化加载所有数据用于概览显示
  fetchUsers();
  fetchDevices();
  fetchRecords();
});
</script>

<style scoped>
.admin-container {
  height: 100vh;
  background-color: #f9fafb;
}

.admin-layout {
  height: 100%;
}

.admin-aside {
  background-color: #111827;
  display: flex;
  flex-direction: column;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  background-color: #111827;
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  border-bottom: 1px solid #1f2937;
}

.admin-menu {
  border-right: none;
  flex: 1;
}

.aside-footer {
  padding: 20px;
  border-top: 1px solid #1f2937;
}

.admin-main {
  padding: 0;
  background-color: #f3f4f6;
}

.main-header {
  height: 64px;
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.main-header h2 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.content-body {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.overview-section {
  margin-bottom: 24px;
}

.stat-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #111827;
  padding: 10px 0;
}

.card-section {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.table-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.settings-hint {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 20px 0;
}
.settings-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

/* 适配 Element Plus 样式 */
:deep(.el-menu-item.is-active) {
  background-color: #374151 !important;
}
:deep(.el-card__header) {
  font-size: 14px;
  color: #6b7280;
  border-bottom: none;
  padding-bottom: 0;
}
</style>
