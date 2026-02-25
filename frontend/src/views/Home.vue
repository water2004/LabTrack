<template>
  <div class="home-container">
    <el-header class="header">
      <div class="logo">LabTrack</div>
      <div class="user-info">
        <el-button type="primary" size="small" @click="showAddDevice = true">+ 录入设备</el-button>
        <span>{{ username }}</span>
        <el-button link @click="logout">登出</el-button>
      </div>
    </el-header>

    <main class="main-content">
      <el-tabs v-model="activeTab" class="custom-tabs">
        <!-- 标签页 1: 设备列表 -->
        <el-tab-pane label="设备浏览" name="devices">
          <div class="filter-bar">
            <el-radio-group v-model="deviceFilter" size="small">
              <el-radio-button label="all">全部设备</el-radio-button>
              <el-radio-button label="mine">我负责的</el-radio-button>
            </el-radio-group>
            <el-input 
              v-model="searchQuery" 
              placeholder="搜索名称/资产号" 
              size="small" 
              style="width: 200px; margin-left: 10px;" 
              @input="fetchDevices"
              clearable
            />
          </div>
          <el-row :gutter="20">
            <el-col v-for="device in filteredDevices" :key="device.id" :xs="24" :sm="12" :md="8" :lg="6">
              <el-card class="device-card" :body-style="{ padding: '0px' }" @click="device.status === 0 && toggleSelection(device)">
                <div class="image-placeholder">
                  <img v-if="device.image_path" :src="`http://localhost:8000${device.image_path}`" class="device-img" />
                  <div v-else class="no-img">No Image</div>
                  <div class="status-tag" :class="statusClass(device.status)">
                    {{ statusText(device.status) }}
                  </div>
                  <div v-if="isSelected(device.id)" class="selected-overlay">
                    <el-icon size="30" color="#fff"><Check /></el-icon>
                  </div>
                </div>
                <div style="padding: 14px">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-code">资产号: {{ device.asset_code }}</div>
                  <div class="device-footer">
                    <span class="manager">负责人: {{ device.manager || '无' }}</span>
                    <el-button 
                      v-if="device.status === 0" 
                      :type="isSelected(device.id) ? 'success' : 'primary'" 
                      size="small" 
                      plain
                    >
                      {{ isSelected(device.id) ? '已选中' : '+ 加入' }}
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 标签页 2: 实验管理 -->
        <el-tab-pane label="实验管理" name="experiments">
          <div class="section-title">🚀 进行中的实验 ({{ activeGroups.length }})</div>
          <el-empty v-if="activeGroups.length === 0" description="暂无运行中的实验" :image-size="60" />
          <el-row :gutter="20">
            <el-col v-for="group in activeGroups" :key="group.group_id" :span="24">
              <el-card class="active-exp-card" style="margin-bottom: 15px;">
                <template #header>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: #909399;">开始时间: {{ formatTime(group.start_time) }}</span>
                    <el-button type="danger" size="small" @click="stopGroup(group)">结束该实验</el-button>
                  </div>
                </template>
                <div class="exp-devices">
                  <el-tag v-for="dev in group.devices" :key="dev.id" size="small" style="margin-right: 8px; margin-bottom: 5px;">
                    {{ dev.name }}
                  </el-tag>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-divider />

          <div class="section-title">⭐ 预设组合</div>
          <el-empty v-if="presets.length === 0" description="暂无保存的预设" :image-size="60" />
          <el-row :gutter="20">
            <el-col v-for="preset in presets" :key="preset.id" :span="24">
              <el-card class="preset-card" style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <div class="preset-name">{{ preset.name }}</div>
                  <div>
                    <el-button type="primary" size="small" @click="applyPreset(preset)">加载</el-button>
                    <el-button type="danger" size="small" link @click="deletePreset(preset.id)">删除</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 录入设备弹窗 -->
    <el-dialog v-model="showAddDevice" title="录入新设备" width="90%">
      <el-form :model="newDevice" label-width="80px" label-position="top">
        <el-form-item label="设备名称">
          <el-input v-model="newDevice.name" placeholder="如: 恒温摇床" />
        </el-form-item>
        <el-form-item label="资产编号">
          <el-input v-model="newDevice.asset_code" placeholder="扫描或输入资产标签号" />
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="newDevice.location" placeholder="如: 302实验室" />
        </el-form-item>
        <el-form-item label="设备照片">
          <input type="file" accept="image/*" capture="environment" @change="handleFileUpload" style="width: 100%" />
          <p style="font-size: 12px; color: #909399;">支持拍照上传</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDevice = false">取消</el-button>
        <el-button type="primary" @click="addDevice" :loading="loading">确认录入</el-button>
      </template>
    </el-dialog>

    <!-- 已选设备浮动条 (购物车模式) -->
    <div v-if="selectedDevices.length > 0" class="selection-drawer">
      <div class="selection-header">
        <span class="selection-names">已选 ({{ selectedDevices.length }}): {{ selectedNames }}</span>
        <div class="selection-actions">
          <el-button type="info" size="small" plain @click="promptSavePreset">存为预设</el-button>
          <el-button type="success" size="small" @click="startExperiment">开始实验</el-button>
        </div>
      </div>
    </div>

    <!-- 实验开启成功弹窗 (带链接) -->
    <el-dialog v-model="showLinkDialog" title="实验已开启" width="300px">
      <p>您可以收藏此链接，下次一键复用此组合：</p>
      <el-input v-model="shareLink" readonly>
        <template #append>
          <el-button @click="copyLink">复制</el-button>
        </template>
      </el-input>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { Search, Check, VideoPlay } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const username = localStorage.getItem('username');
const router = useRouter();
const devices = ref<any[]>([]);
const activeGroups = ref<any[]>([]);
const selectedDevices = ref<any[]>([]);
const searchQuery = ref('');
const activeTab = ref('devices');
const deviceFilter = ref('all');
const presets = ref<any[]>([]);

const filteredDevices = computed(() => {
  let list = devices.value;
  if (deviceFilter.value === 'mine') {
    list = list.filter(d => d.manager === username);
  }
  return list;
});

const showAddDevice = ref(false);
const loading = ref(false);
const newDevice = ref({ name: '', asset_code: '', location: '', manager: username });
const selectedFile = ref<File | null>(null);

const showLinkDialog = ref(false);
const shareLink = ref('');

const fetchDevices = async () => {
  const res = await api.get('/devices', { params: { q: searchQuery.value } });
  devices.value = res.data;
};

const fetchActiveGroups = async () => {
  const res = await api.get('/users/me/active-groups', { params: { username } });
  activeGroups.value = res.data;
};

const stopGroup = async (group: any) => {
  ElMessageBox.confirm(`确定要结束该实验吗？(包含 ${group.devices.length} 台设备)`, '提示').then(async () => {
    try {
      const ids = group.devices.map((d: any) => d.id);
      await api.post(`/experiment/stop?username=${username}`, { device_ids: ids });
      ElMessage.success('实验已结束');
      fetchDevices();
      fetchActiveGroups();
    } catch (err) {
      ElMessage.error('结束失败');
    }
  });
};

const formatTime = (timeStr: string) => {
  const d = new Date(timeStr);
  return d.toLocaleString('zh-CN', { hour12: false });
};

const fetchPresets = async () => {
  const res = await api.get('/presets', { params: { username } });
  presets.value = res.data;
};

const promptSavePreset = () => {
  ElMessageBox.prompt('请输入预设名称', '保存预设', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  }).then(async ({ value }) => {
    if (!value) return;
    const ids = selectedDevices.value.map(d => d.id).join(',');
    await api.post(`/presets?username=${username}`, { name: value, device_ids: ids });
    ElMessage.success('预设已保存');
    fetchPresets();
  });
};

const applyPreset = (preset: any) => {
  const ids = preset.device_ids.split(',').map((id: string) => parseInt(id));
  selectedDevices.value = devices.value.filter(d => ids.includes(d.id) && d.status === 0);
  activeTab.value = 'devices';
  ElMessage.success(`已加载预设: ${preset.name}`);
};

const deletePreset = async (id: number) => {
  await api.delete(`/presets/${id}?username=${username}`);
  ElMessage.success('预设已删除');
  fetchPresets();
};

const statusText = (status: number) => {
  if (status === 0) return '闲置';
  if (status === 1) return '使用中';
  return '故障';
};

const statusClass = (status: number) => {
  if (status === 0) return 'status-idle';
  if (status === 1) return 'status-busy';
  return 'status-error';
};

const isSelected = (id: number) => selectedDevices.value.some(d => d.id === id);

const selectedNames = computed(() => selectedDevices.value.map(d => d.name).join('、'));

const toggleSelection = (device: any) => {
  const index = selectedDevices.value.findIndex(d => d.id === device.id);
  if (index > -1) {
    selectedDevices.value.splice(index, 1);
  } else {
    selectedDevices.value.push(device);
  }
};

const handleFileUpload = (event: any) => {
  selectedFile.value = event.target.files[0];
};

const addDevice = async () => {
  if (!newDevice.value.name || !newDevice.value.asset_code) {
    return ElMessage.warning('请填写名称和资产编号');
  }
  loading.value = true;
  const formData = new FormData();
  formData.append('name', newDevice.value.name);
  formData.append('asset_code', newDevice.value.asset_code);
  formData.append('location', newDevice.value.location || '');
  formData.append('manager', username || '');
  if (selectedFile.value) {
    formData.append('image', selectedFile.value);
  }

  try {
    await api.post('/admin/devices', formData);
    ElMessage.success('设备录入成功');
    showAddDevice.value = false;
    newDevice.value = { name: '', asset_code: '', location: '', manager: username };
    selectedFile.value = null;
    fetchDevices();
  } catch (err) {
    ElMessage.error('录入失败，资产编号可能已存在');
  } finally {
    loading.value = false;
  }
};

const startExperiment = async () => {
  try {
    const ids = selectedDevices.value.map(d => d.id);
    await api.post(`/experiment/start?username=${username}`, { device_ids: ids });
    
    // 生成分享链接
    const baseUrl = window.location.origin + window.location.pathname;
    shareLink.value = `${baseUrl}?ids=${ids.join(',')}`;
    
    selectedDevices.value = [];
    showLinkDialog.value = true;
    
    fetchDevices();
    fetchActiveGroups();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '启动失败');
  }
};

// stopExperiment removed

const copyLink = () => {
  navigator.clipboard.writeText(shareLink.value);
  ElMessage.success('链接已复制到剪贴板');
};

const logout = () => {
  localStorage.clear();
  router.push('/login');
};

onMounted(() => {
  fetchDevices();
  fetchActiveGroups();
  fetchPresets();
  
  const urlParams = new URLSearchParams(window.location.search);
  const scanId = urlParams.get('id');
  const batchIds = urlParams.get('ids');

  if (scanId) {
    // 扫码直连逻辑 (单机模式)
    const idNum = parseInt(scanId);
    api.get('/devices').then(res => {
      const device = res.data.find((d: any) => d.id === idNum);
      if (device && device.status === 0) {
        selectedDevices.value = [device];
        ElMessage.info(`扫码选中: ${device.name}`);
      }
    });
  } else if (batchIds) {
    // 一键复用逻辑
    const ids = batchIds.split(',').map(id => parseInt(id));
    api.get('/devices').then(res => {
      selectedDevices.value = res.data.filter((d: any) => ids.includes(d.id) && d.status === 0);
      if (selectedDevices.value.length > 0) {
        ElMessage.success(`已恢复上次组合: ${selectedNames.value}`);
      }
    });
  }
});
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background-color: #f0f2f5;
  padding-bottom: 80px; /* 为底部抽屉留出空间 */
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}
.logo {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}
.search-box {
  width: 40%;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.active-bar {
  background: #fdf6ec;
  border-bottom: 1px solid #faecd8;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.active-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e6a23c;
  font-weight: bold;
}
.main-content {
  padding: 10px 20px;
}
.filter-bar {
  margin-bottom: 15px;
  display: flex;
  justify-content: center;
}
.device-card {
  margin-bottom: 20px;
  cursor: pointer;
  position: relative;
}
.image-placeholder {
  height: 150px;
  background: #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.device-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.selected-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(103, 194, 58, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.status-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
  z-index: 10;
}
.status-idle { background: #67C23A; }
.status-busy { background: #F56C6C; }
.status-error { background: #909399; }

.device-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}
.device-code {
  font-size: 13px;
  color: #909399;
}
.device-footer {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.manager {
  font-size: 12px;
  color: #606266;
}

.section-title {
  font-weight: bold;
  margin: 15px 0;
  color: #303133;
}
.active-exp-card {
  border-left: 4px solid #409EFF;
}
.exp-time {
  font-size: 13px;
  color: #909399;
}

/* 底部抽屉样式 */
.selection-drawer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
  padding: 15px 20px;
  z-index: 1000;
}
.selection-header {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.selection-names {
  flex: 1;
  font-weight: bold;
  color: #409EFF;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 15px;
}
.selection-actions {
  display: flex;
  gap: 10px;
}
</style>

