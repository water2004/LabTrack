<template>
  <div class="admin-container">
    <el-container class="admin-layout">
      <el-aside width="240px" class="admin-aside">
        <div class="logo-area">
          <el-icon :size="24" color="#fff"><ElementPlus /></el-icon>
          <h2>LabTrack</h2>
        </div>
        <el-menu 
          default-active="1" 
          class="admin-menu"
          background-color="#1f2937"
          text-color="#9ca3af"
          active-text-color="#fff"
        >
          <div class="menu-label">管理中心</div>
          <el-menu-item index="1" @click="activeTab = 'devices'">
            <el-icon><Monitor /></el-icon> <span>设备管理</span>
          </el-menu-item>
          <el-menu-item index="2" @click="activeTab = 'users'">
            <el-icon><User /></el-icon> <span>用户名单</span>
          </el-menu-item>
          <el-menu-item index="3" @click="activeTab = 'records'">
            <el-icon><DataLine /></el-icon> <span>使用记录</span>
          </el-menu-item>
          
          <div class="menu-divider"></div>
          
          <el-menu-item index="4" @click="logout" class="logout-item">
            <el-icon><SwitchButton /></el-icon> <span>退出登录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main class="admin-content">
        <div class="content-wrapper">
          <!-- 设备管理 -->
          <div v-if="activeTab === 'devices'">
            <div class="page-header">
              <div>
                <h2>设备库</h2>
                <p class="subtitle">管理实验室所有固定资产</p>
              </div>
              <el-button type="primary" size="large" @click="showAddDevice = true" :icon="Plus">新增设备</el-button>
            </div>
            
            <el-card shadow="never" class="table-card">
              <el-table :data="devices" stripe style="width: 100%" :header-cell-style="{background:'#f9fafb', color:'#374151'}">
                <el-table-column prop="asset_code" label="资产编号" width="150">
                  <template #default="{ row }">
                    <span class="mono-code">{{ row.asset_code }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="设备名称">
                  <template #default="{ row }">
                    <span class="device-name">{{ row.name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="location" label="位置" />
                <el-table-column prop="manager" label="负责人" />
                <el-table-column label="状态" width="120">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 0 ? 'success' : 'danger'" effect="dark" round>
                      {{ scope.row.status === 0 ? '闲置' : '使用中' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="scope">
                    <el-button link type="primary" @click="viewQR(scope.row.id)">
                      <el-icon><files /></el-icon> 二维码
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 用户管理 -->
          <div v-if="activeTab === 'users'">
            <div class="page-header">
              <div>
                <h2>用户名单</h2>
                <p class="subtitle">允许访问系统的白名单</p>
              </div>
              <el-button type="primary" size="large" @click="showAddUser = true" :icon="Plus">新增用户</el-button>
            </div>
            <el-card shadow="never" class="table-card">
              <el-table :data="users" stripe style="width: 100%" :header-cell-style="{background:'#f9fafb', color:'#374151'}">
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="username" label="用户名">
                  <template #default="{ row }">
                    <div class="user-cell">
                      <div class="avatar-sm">{{ row.username.charAt(0).toUpperCase() }}</div>
                      <span>{{ row.username }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="注册时间">
                  <template #default="{ row }">
                    {{ new Date(row.created_at).toLocaleDateString() }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 记录查询 -->
          <div v-if="activeTab === 'records'">
            <div class="page-header">
              <div>
                <h2>使用记录</h2>
                <p class="subtitle">查询历史实验数据</p>
              </div>
              <div class="filter-group">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                  @change="fetchRecords"
                  size="default"
                />
                <el-button type="success" size="default" @click="exportExcel" :icon="Download">导出 Excel</el-button>
              </div>
            </div>
            <el-card shadow="never" class="table-card">
              <el-table :data="records" stripe height="600" style="width: 100%" :header-cell-style="{background:'#f9fafb', color:'#374151'}">
                <el-table-column prop="asset_code" label="资产编号" width="140" />
                <el-table-column prop="device_name" label="设备名" width="180" />
                <el-table-column prop="user_name" label="使用者" width="120" />
                <el-table-column prop="start_time" label="开始时间" width="180">
                  <template #default="{ row }">
                    {{ new Date(row.start_time).toLocaleString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="end_time" label="结束时间" width="180">
                  <template #default="{ row }">
                    {{ new Date(row.end_time).toLocaleString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="duration" label="时长">
                  <template #default="{ row }">
                    <el-tag type="info" size="small">{{ (row.duration / 60).toFixed(1) }} 分钟</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="notes" label="备注" />
              </el-table>
            </el-card>
          </div>
        </div>
      </el-main>
    </el-container>

    <!-- Dialogs -->
    <el-dialog v-model="showAddDevice" title="新增设备" width="500px" center>
      <el-form :model="newDevice" label-width="80px" label-position="top">
        <el-form-item label="名称">
          <el-input v-model="newDevice.name" size="large" />
        </el-form-item>
        <el-form-item label="资产编号">
          <el-input v-model="newDevice.asset_code" size="large" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="位置">
              <el-input v-model="newDevice.location" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
             <el-form-item label="负责人">
              <el-input v-model="newDevice.manager" size="large" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="图片">
          <input type="file" @change="handleFileUpload" class="file-input" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDevice = false" size="large">取消</el-button>
        <el-button type="primary" @click="addDevice" size="large">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddUser" title="新增用户" width="400px" center>
      <el-form label-width="80px" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="newUsername" size="large" placeholder="请输入用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddUser = false" size="large">取消</el-button>
        <el-button type="primary" @click="addUser" size="large">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { ElMessage } from 'element-plus';
import { 
  ElementPlus, Monitor, User, DataLine, SwitchButton, 
  Plus, Download, Files 
} from '@element-plus/icons-vue';

const router = useRouter();
const activeTab = ref('devices');
const devices = ref([]);
const users = ref([]);
const records = ref([]);
const dateRange = ref([]);

const showAddDevice = ref(false);
const newDevice = ref({ name: '', asset_code: '', location: '', manager: '' });
const selectedFile = ref<File | null>(null);
const showAddUser = ref(false);
const newUsername = ref('');

const fetchDevices = async () => {
  const res = await api.get('/devices');
  devices.value = res.data;
};

const fetchUsers = async () => {
  const res = await api.get('/admin/users');
  users.value = res.data;
};

const fetchRecords = async () => {
  const params: any = {};
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0];
    params.end_date = dateRange.value[1];
  }
  const res = await api.get('/admin/records', { params });
  records.value = res.data;
};

const handleFileUpload = (event: any) => {
  selectedFile.value = event.target.files[0];
};

const addDevice = async () => {
  const formData = new FormData();
  formData.append('name', newDevice.value.name);
  formData.append('asset_code', newDevice.value.asset_code);
  formData.append('location', newDevice.value.location);
  formData.append('manager', newDevice.value.manager);
  if (selectedFile.value) {
    formData.append('image', selectedFile.value);
  }

  try {
    await api.post('/admin/devices', formData);
    ElMessage.success('设备添加成功');
    showAddDevice.value = false;
    fetchDevices();
  } catch (err) {
    ElMessage.error('添加失败');
  }
};

const addUser = async () => {
  try {
    await api.post('/admin/users', { username: newUsername.value });
    ElMessage.success('用户添加成功');
    showAddUser.value = false;
    newUsername.value = '';
    fetchUsers();
  } catch (err) {
    ElMessage.error('添加失败');
  }
};

const exportExcel = () => {
  let url = 'http://localhost:8000/admin/export';
  if (dateRange.value && dateRange.value.length === 2) {
    url += `?start_date=${dateRange.value[0]}&end_date=${dateRange.value[1]}`;
  }
  window.open(url, '_blank');
};

const viewQR = (id: number) => {
  const url = `http://localhost:5173/?id=${id}`;
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(url)}`;
  window.open(qrUrl, '_blank');
};

const logout = () => {
  localStorage.clear();
  router.push('/login');
};

onMounted(() => {
  fetchDevices();
  fetchUsers();
  fetchRecords();
});
</script>

<style scoped>
.admin-container {
  height: 100vh;
  background-color: #f3f4f6;
}
.admin-layout {
  height: 100%;
}
.admin-aside {
  background-color: #1f2937;
  color: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 10px rgba(0,0,0,0.1);
  z-index: 10;
}
.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background-color: #111827;
}
.logo-area h2 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 1px;
}
.admin-menu {
  flex: 1;
  border-right: none;
  padding-top: 20px;
}
.menu-label {
  padding: 0 20px 10px;
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  font-weight: 600;
}
.menu-divider {
  height: 1px;
  background: #374151;
  margin: 10px 20px;
}

.admin-content {
  padding: 0;
  background-color: #f3f4f6;
  overflow-y: auto;
}
.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  color: #111827;
}
.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.table-card {
  border-radius: 8px;
  overflow: hidden;
  border: none;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.mono-code {
  font-family: 'Courier New', monospace;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  color: #374151;
}
.device-name {
  font-weight: 600;
  color: #1f2937;
}
.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar-sm {
  width: 28px;
  height: 28px;
  background: #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: #4b5563;
}

.filter-group {
  display: flex;
  gap: 12px;
}
.file-input {
  padding: 10px;
  border: 1px dashed #d1d5db;
  width: 100%;
  border-radius: 6px;
  background: #f9fafb;
}
</style>
