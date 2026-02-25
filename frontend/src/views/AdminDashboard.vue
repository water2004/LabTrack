<template>
  <div class="admin-container">
    <el-container>
      <el-aside width="200px" class="aside">
        <h3 style="text-align: center;">管理后台</h3>
        <el-menu default-active="1">
          <el-menu-item index="1" @click="activeTab = 'devices'">设备管理</el-menu-item>
          <el-menu-item index="2" @click="activeTab = 'users'">用户管理</el-menu-item>
          <el-menu-item index="3" @click="activeTab = 'records'">使用记录</el-menu-item>
          <el-menu-item index="4" @click="logout">退出登录</el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <!-- ... 设备管理和用户管理保持不变 ... -->
        <div v-if="activeTab === 'devices'">
          <!-- (原有代码) -->
          <div class="tab-header">
            <h2>设备列表</h2>
            <el-button type="primary" @click="showAddDevice = true">新增设备</el-button>
          </div>
          <el-table :data="devices" border>
            <el-table-column prop="asset_code" label="资产编号" width="150" />
            <el-table-column prop="name" label="设备名称" />
            <el-table-column prop="location" label="位置" />
            <el-table-column prop="manager" label="负责人" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 0 ? 'success' : 'danger'">
                  {{ scope.row.status === 0 ? '闲置' : '使用中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button link type="primary" @click="viewQR(scope.row.id)">二维码</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="activeTab === 'users'">
          <div class="tab-header">
            <h2>用户列表</h2>
            <el-button type="primary" @click="showAddUser = true">新增用户</el-button>
          </div>
          <el-table :data="users" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="created_at" label="注册时间" />
          </el-table>
        </div>

        <div v-if="activeTab === 'records'">
          <div class="tab-header">
            <h2>实验室使用记录</h2>
            <div class="filter-actions">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                @change="fetchRecords"
                size="small"
                style="margin-right: 10px;"
              />
              <el-button type="success" size="small" @click="exportExcel">导出 Excel</el-button>
            </div>
          </div>
          <el-table :data="records" border stripe height="500">
            <el-table-column prop="asset_code" label="资产编号" width="120" />
            <el-table-column prop="device_name" label="设备名" />
            <el-table-column prop="user_name" label="使用者" width="100" />
            <el-table-column prop="start_time" label="开始时间" width="160" />
            <el-table-column prop="end_time" label="结束时间" width="160" />
            <el-table-column prop="duration" label="时长(秒)" width="100" />
          </el-table>
        </div>
      </el-main>
    </el-container>

    <!-- Add Device Dialog -->
    <el-dialog v-model="showAddDevice" title="新增设备">
      <el-form :model="newDevice" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="newDevice.name" />
        </el-form-item>
        <el-form-item label="资产编号">
          <el-input v-model="newDevice.asset_code" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="newDevice.location" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="newDevice.manager" />
        </el-form-item>
        <el-form-item label="图片">
          <input type="file" @change="handleFileUpload" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDevice = false">取消</el-button>
        <el-button type="primary" @click="addDevice">提交</el-button>
      </template>
    </el-dialog>

    <!-- Add User Dialog -->
    <el-dialog v-model="showAddUser" title="新增用户">
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="newUsername" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddUser = false">取消</el-button>
        <el-button type="primary" @click="addUser">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const activeTab = ref('devices');
const devices = ref([]);
const users = ref([]);
const records = ref([]);
const dateRange = ref([]);

// Add Device
const showAddDevice = ref(false);
const newDevice = ref({ name: '', asset_code: '', location: '', manager: '' });
const selectedFile = ref<File | null>(null);

// Add User
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

const fetchRecords = async () => {
  const params: any = {};
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0];
    params.end_date = dateRange.value[1];
  }
  const res = await api.get('/admin/records', { params });
  records.value = res.data;
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
}
.aside {
  background-color: #304156;
  color: #fff;
}
.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
:deep(.el-menu) {
  border-right: none;
}
</style>
