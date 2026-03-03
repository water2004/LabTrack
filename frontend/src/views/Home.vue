<template>
  <div class="home-container">
    <el-header class="custom-header">
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon :size="20" color="#fff"><ElementPlus /></el-icon>
        </div>
        <span class="brand-name">LabTrack</span>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" bg round size="default" @click="showAddDevice = true" class="add-btn">
          <el-icon style="margin-right: 5px"><Plus /></el-icon> 录入设备
        </el-button>
        
        <el-dropdown trigger="click">
          <div class="user-avatar">
            {{ username?.charAt(0).toUpperCase() }}
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>{{ username }}</el-dropdown-item>
              <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <main class="main-content">
      <el-tabs v-model="activeTab" class="modern-tabs">
        <!-- 标签页 1: 设备列表 -->
        <el-tab-pane label="设备浏览" name="devices">
          <div class="toolbar">
            <el-radio-group v-model="deviceFilter" size="large" class="custom-radio">
              <el-radio-button label="all">全部设备</el-radio-button>
              <el-radio-button label="mine">我负责的</el-radio-button>
            </el-radio-group>
            
            <el-input 
              v-model="searchQuery" 
              placeholder="搜索设备名称或资产号..." 
              size="large" 
              class="search-input"
              @input="fetchDevices"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <el-row :gutter="24">
            <el-col v-for="device in filteredDevices" :key="device.id" :xs="24" :sm="12" :md="8" :lg="6">
              <div 
                class="device-card-modern" 
                :class="{ 'is-selected': isSelected(device.id), 'is-disabled': device.status !== 0 }"
                @click="device.status === 0 && toggleSelection(device)"
              >
                <div class="card-image-wrapper">
                  <img v-if="device.image_path" :src="`http://localhost:8000${device.image_path}`" class="device-img" />
                  <div v-else class="no-img-placeholder">
                    <el-icon :size="40" color="#dcdfe6"><Picture /></el-icon>
                  </div>
                  
                  <div class="status-badge" :class="statusClass(device.status)">
                    {{ statusText(device.status) }}
                  </div>
                  
                  <div class="selection-indicator" v-if="isSelected(device.id)">
                    <el-icon color="#fff" :size="24"><Check /></el-icon>
                  </div>
                </div>
                
                <div class="card-content">
                  <div class="card-header">
                    <h3 class="device-name">{{ device.name }}</h3>
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="asset-code">{{ device.asset_code }}</span>
                      <el-button 
                        v-if="device.manager === username" 
                        link 
                        type="primary" 
                        style="padding: 0;"
                        @click.stop="openEdit(device)"
                      >
                        <el-icon><Edit /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  
                  <div class="card-meta">
                    <div class="meta-item">
                      <el-icon><Location /></el-icon>
                      <span>{{ device.location || '未登记位置' }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><User /></el-icon>
                      <span>{{ device.manager || '无负责人' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 标签页 2: 实验管理 -->
        <el-tab-pane label="实验管理" name="experiments">
          <div class="experiments-container">
            <div class="section-header">
              <h3>🚀 进行中的实验 <span class="count-badge">{{ activeGroups.length }}</span></h3>
            </div>
            
            <el-empty v-if="activeGroups.length === 0" description="暂无运行中的实验" :image-size="100" />
            
            <div class="active-experiments-grid">
              <div v-for="group in activeGroups" :key="group.group_id" class="experiment-card">
                <div class="exp-header">
                  <div class="time-info">
                    <span class="label">开始时间: {{ formatTime(group.start_time) }}</span>
                    <span class="value" v-if="group.notes" style="font-size: 13px; color: #409EFF; margin-top: 4px;">
                      📝 备注: {{ group.notes }}
                    </span>
                  </div>
                  <el-button type="danger" plain size="small" round @click="stopGroup(group)">结束实验</el-button>
                </div>
                <div class="exp-divider"></div>
                <div class="exp-devices-list">
                  <div v-for="dev in group.devices" :key="dev.id" class="exp-device-item">
                    <div class="dot"></div>
                    <span>{{ dev.name }}</span>
                    <span class="code">{{ dev.asset_code }}</span>
                  </div>
                </div>
              </div>
            </div>

            <el-divider class="section-divider" />

            <div class="section-header">
              <h3>⭐ 预设组合 <span class="count-badge secondary">{{ presets.length }}</span></h3>
            </div>
            
            <el-empty v-if="presets.length === 0" description="暂无保存的预设" :image-size="80" />
            
            <div class="presets-grid">
              <div v-for="preset in presets" :key="preset.id" class="preset-card-modern">
                <div class="preset-icon">
                  <el-icon><Collection /></el-icon>
                </div>
                <div class="preset-info">
                  <h4>{{ preset.name }}</h4>
                  <p v-if="preset.notes" style="font-size: 12px; color: #409EFF; margin-bottom: 2px;">📝 {{ preset.notes }}</p>
                  <p>{{ preset.device_ids.split(',').length }} 台设备</p>
                </div>
                <div class="preset-actions">
                  <el-button type="primary" circle size="small" @click="applyPreset(preset)">
                    <el-icon><VideoPlay /></el-icon>
                  </el-button>
                  <el-button type="info" plain circle size="small" @click="openEditPreset(preset)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button type="danger" circle plain size="small" @click="deletePreset(preset.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <div class="admin-footer">
        <el-link type="info" :underline="false" @click="$router.push('/admin-login')">
          <el-icon><Setting /></el-icon> 管理后台
        </el-link>
      </div>
    </main>

    <!-- 录入设备弹窗 -->
    <el-dialog v-model="showAddDevice" title="录入新设备" width="500px" center>
      <div class="photo-capture-area">
        <div class="preview-box" @click="$refs.fileInputAdd.click()">
          <img v-if="previewUrl" :src="previewUrl" class="preview-img" />
          <div v-else class="preview-placeholder">
            <el-icon :size="40"><Camera /></el-icon>
            <p>点击拍照或选择照片</p>
          </div>
          <input type="file" ref="fileInputAdd" hidden accept="image/*" capture="environment" @change="handleFileUpload" />
        </div>
      </div>
      
      <el-form :model="newDevice" label-width="80px" label-position="top">
        <el-form-item label="设备名称">
          <el-input v-model="newDevice.name" placeholder="如: 恒温摇床" />
        </el-form-item>
        <el-form-item label="资产编号 (可选)">
          <div style="display: flex; gap: 8px;">
            <el-input v-model="newDevice.asset_code" placeholder="扫描或输入资产标签号" />
            <el-button type="primary" plain @click="openScanner('add')">
               <el-icon><FullScreen /></el-icon> 扫码
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="newDevice.location" placeholder="如: 302" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDevice = false">取消</el-button>
        <el-button type="primary" @click="addDevice" :loading="loading">确认录入</el-button>
      </template>
    </el-dialog>

    <!-- 编辑设备弹窗 -->
    <el-dialog v-model="showEditDevice" title="修改设备信息" width="450px" center>
      <div class="photo-capture-area">
        <div class="preview-box" @click="$refs.fileInputEdit.click()">
          <img v-if="previewUrl" :src="previewUrl" class="preview-img" />
          <div v-else class="preview-placeholder">
            <el-icon :size="40"><Camera /></el-icon>
            <p>点击更换照片</p>
          </div>
          <input type="file" ref="fileInputEdit" hidden accept="image/*" capture="environment" @change="handleFileUpload" />
        </div>
      </div>

      <el-form :model="editingDevice" label-width="80px" label-position="top">
        <el-form-item label="系统 ID (UUID)">
          <el-tag type="info">{{ editingDevice.uuid }}</el-tag>
          <span style="font-size: 12px; color: #909399; margin-left: 8px;">(永久唯一标识)</span>
        </el-form-item>
        <el-form-item label="资产编号 (Asset Code)">
          <div style="display: flex; gap: 8px;">
            <el-input v-model="editingDevice.asset_code" placeholder="未分配标签" />
            <el-button type="primary" plain @click="openScanner('edit')">
               <el-icon><FullScreen /></el-icon> 扫码
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="editingDevice.name" />
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="editingDevice.location" />
        </el-form-item>
        <el-form-item label="负责人转让">
          <el-select v-model="editingDevice.manager" placeholder="选择新的负责人" style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.username"
              :value="user.username"
            />
          </el-select>
          <p style="font-size: 12px; color: #F56C6C; margin-top: 4px;" v-if="editingDevice.manager !== username">
            注意：转让后您将失去该设备的编辑权限
          </p>
        </el-form-item>
        <el-form-item label="设备状态">
          <el-select v-model="editingDevice.status" style="width: 100%">
            <el-option :value="0" label="闲置 (正常使用)" />
            <el-option :value="1" label="使用中 (锁定)" />
            <el-option :value="2" label="借出中 (外部借阅)" />
            <el-option :value="3" label="故障 (不可用)" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDevice = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="loading">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 条形码扫描模拟/对话框 -->
    <el-dialog 
      v-model="scannerVisible" 
      title="扫描条形码/二维码" 
      width="90%" 
      style="max-width: 400px" 
      center 
      append-to-body 
      @opened="startCamera" 
      @closed="handleScannerClose"
    >
      <div style="text-align: center;">
        <div id="reader" style="width: 100%; border-radius: 8px; overflow: hidden;"></div>
        <p style="margin-top: 15px; font-size: 14px; color: #606266;">将条码置于框内即可自动识别</p>
      </div>
    </el-dialog>

    <!-- 编辑预设弹窗 -->
    <el-dialog v-model="showEditPreset" title="编辑实验预设" width="400px" center>
      <el-form :model="editingPreset" label-width="80px" label-position="top">
        <el-form-item label="预设名称">
          <el-input v-model="editingPreset.name" />
        </el-form-item>
        <el-form-item label="包含设备">
          <el-select
            v-model="editingPreset.device_ids_array"
            multiple
            filterable
            placeholder="搜索并选择设备"
            style="width: 100%"
          >
            <el-option
              v-for="item in devices"
              :key="item.id"
              :label="`${item.name} (${item.asset_code})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预设备注">
          <el-input v-model="editingPreset.notes" type="textarea" placeholder="备注实验用途、注意事项等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditPreset = false">取消</el-button>
        <el-button type="primary" @click="handleUpdatePreset" :loading="loading">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 底部浮动栏 (购物车) -->
    <transition name="slide-up">
      <div v-if="selectedDevices.length > 0" class="floating-cart">
        <div class="cart-content">
          <div class="cart-info">
            <span class="count">{{ selectedDevices.length }}</span>
            <span class="label">已选设备</span>
            <div class="device-preview">{{ selectedNames }}</div>
          </div>
          <div class="cart-actions">
            <el-button type="info" plain round @click="promptSavePreset">存为预设</el-button>
            <el-button type="primary" round class="start-btn" @click="startExperiment">
              立即开始 <el-icon class="el-icon--right"><Right /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 实验开启成功弹窗 -->
    <el-dialog v-model="showLinkDialog" title="实验已开启" width="400px" center>
      <div style="text-align: center; margin-bottom: 20px;">
        <el-icon :size="50" color="#67C23A"><CircleCheckFilled /></el-icon>
        <p style="font-size: 16px; margin-top: 10px;">实验开始成功！</p>
      </div>
      <p style="color: #909399; font-size: 13px;">您可以收藏此链接，下次一键复用此组合：</p>
      <el-input v-model="shareLink" readonly size="large">
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
import { Html5Qrcode } from 'html5-qrcode';
import { 
  Search, Check, VideoPlay, Plus, Picture, Location, User, 
  Right, CircleCheckFilled, Collection, Delete, ElementPlus,
  Edit, Setting, Files, Camera, FullScreen
} from '@element-plus/icons-vue';
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

const users = ref<any[]>([]);
const showAddDevice = ref(false);
const showEditDevice = ref(false);
const showEditPreset = ref(false);
const editingDevice = ref<any>({});
const editingPreset = ref<any>({});
const loading = ref(false);
const newDevice = ref({ name: '', asset_code: '', location: '', manager: username });
const selectedFile = ref<File | null>(null);

const showLinkDialog = ref(false);
const shareLink = ref('');
const pendingNotes = ref('');

// 扫码相关
const scannerVisible = ref(false);
const scannerTarget = ref<'add' | 'edit'>('add');
let html5QrCode: Html5Qrcode | null = null;

const openScanner = (target: 'add' | 'edit') => {
  scannerTarget.value = target;
  scannerVisible.value = true;
};

const startCamera = async () => {
  html5QrCode = new Html5Qrcode("reader");
  const config = { fps: 10, qrbox: { width: 250, height: 250 } };
  
  try {
    await html5QrCode.start(
      { facingMode: "environment" }, 
      config,
      (decodedText) => {
        // 扫码成功回调
        if (scannerTarget.value === 'add') {
          newDevice.value.asset_code = decodedText;
        } else {
          editingDevice.value.asset_code = decodedText;
        }
        stopCamera();
        scannerVisible.value = false;
        ElMessage.success('识别成功: ' + decodedText);
      },
      (errorMessage) => {
        // 扫码中，暂无结果
      }
    );
  } catch (err) {
    ElMessage.error('无法启动摄像头，请确保已授权');
    scannerVisible.value = false;
  }
};

const stopCamera = async () => {
  if (html5QrCode) {
    try {
      await html5QrCode.stop();
      html5QrCode = null;
    } catch (err) {
      console.error(err);
    }
  }
};

const handleScannerClose = () => {
  stopCamera();
};

const filteredDevices = computed(() => {
  let list = devices.value;
  if (deviceFilter.value === 'mine') {
    list = list.filter(d => d.manager === username);
  }
  return list;
});

const fetchDevices = async () => {
  const res = await api.get('/devices', { params: { q: searchQuery.value } });
  devices.value = res.data;
};

const fetchUsers = async () => {
  const res = await api.get('/admin/users');
  users.value = res.data;
};

const fetchActiveGroups = async () => {
  const res = await api.get('/users/me/active-groups', { params: { username } });
  activeGroups.value = res.data;
};

const fetchPresets = async () => {
  const res = await api.get('/presets', { params: { username } });
  presets.value = res.data;
};

const statusText = (status: number) => {
  if (status === 0) return '闲置';
  if (status === 1) return '使用中';
  if (status === 2) return '借出中';
  return '故障';
};

const statusClass = (status: number) => {
  if (status === 0) return 'status-idle';
  if (status === 1) return 'status-busy';
  if (status === 2) return 'status-borrow';
  return 'status-error';
};

const isSelected = (id: number) => selectedDevices.value.some(d => d.id === id);

const selectedNames = computed(() => selectedDevices.value.map(d => d.name).join('、'));

const toggleSelection = (device: any) => {
  pendingNotes.value = ''; // 手动修改选择时清空预设带入的备注
  const index = selectedDevices.value.findIndex(d => d.id === device.id);
  if (index > -1) {
    selectedDevices.value.splice(index, 1);
  } else {
    selectedDevices.value.push(device);
  }
};

const previewUrl = ref('');

const handleFileUpload = (event: any) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    previewUrl.value = URL.createObjectURL(file);
  }
};

const openAdd = () => {
  newDevice.value = { name: '', asset_code: '', location: '', manager: username };
  selectedFile.value = null;
  previewUrl.value = '';
  showAddDevice.value = true;
};

const openEdit = (device: any) => {
  editingDevice.value = { ...device };
  previewUrl.value = device.image_path ? `http://localhost:8000${device.image_path}` : '';
  selectedFile.value = null;
  fetchUsers();
  showEditDevice.value = true;
};

const handleUpdate = async () => {
  if (!editingDevice.value.name) return;
  
  // 如果负责人发生变更，增加确认步骤
  if (editingDevice.value.manager !== username) {
    try {
      await ElMessageBox.confirm(
        `确定将该设备转让给 ${editingDevice.value.manager} 吗？转让后您将失去编辑权限。`,
        '确认转让',
        { confirmButtonText: '确定转让', cancelButtonText: '取消', type: 'warning' }
      );
    } catch {
      return;
    }
  }

  loading.value = true;
  try {
    const formData = new FormData();
    formData.append('name', editingDevice.value.name);
    formData.append('location', editingDevice.value.location || '');
    formData.append('manager', editingDevice.value.manager || '');
    formData.append('asset_code', editingDevice.value.asset_code || ''); // 允许为空
    formData.append('status', editingDevice.value.status.toString());
    formData.append('username', username || '');
    if (selectedFile.value) {
      formData.append('image', selectedFile.value);
    }
    
    await api.put(`/devices/${editingDevice.value.id}`, formData);
    ElMessage.success('更新成功');
    showEditDevice.value = false;
    fetchDevices();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '更新失败');
  } finally {
    loading.value = false;
  }
};

const addDevice = async () => {
  if (!newDevice.value.name) {
    return ElMessage.warning('请填写设备名称');
  }
  loading.value = true;
  const formData = new FormData();
  formData.append('name', newDevice.value.name);
  formData.append('asset_code', newDevice.value.asset_code || ''); // 资产编号现在是可选的
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
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '录入失败');
  } finally {
    loading.value = false;
  }
};

const startExperiment = async () => {
  ElMessageBox.prompt('请输入本次实验备注 (必填)', '开始实验', {
    confirmButtonText: '立即开始',
    cancelButtonText: '取消',
    inputPlaceholder: '例如: 观察细胞生长 (项目编号 102)',
    inputValue: pendingNotes.value,
    inputPattern: /\S+/,
    inputErrorMessage: '备注不能为空',
  }).then(async ({ value }) => {
    try {
      const ids = selectedDevices.value.map(d => d.id);
      await api.post(`/experiment/start?username=${username}`, { 
        device_ids: ids,
        notes: value || ''
      });
      
      const baseUrl = window.location.origin + window.location.pathname;
      shareLink.value = `${baseUrl}?ids=${ids.join(',')}`;
      
      selectedDevices.value = [];
      showLinkDialog.value = true;
      
      fetchDevices();
      fetchActiveGroups();
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '启动失败');
    }
  });
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
  const available = devices.value.filter(d => ids.includes(d.id) && d.status === 0);
  
  if (available.length === 0) {
    ElMessage.warning('预设中的设备当前都在使用中或不存在');
    return;
  }
  
  selectedDevices.value = available;
  pendingNotes.value = preset.notes || '';
  activeTab.value = 'devices';
  
  if (available.length < ids.length) {
    ElMessage.warning(`部分设备忙碌，已选中 ${available.length} 台可用设备`);
  } else {
    ElMessage.success(`已加载预设: ${preset.name}`);
  }
};

const deletePreset = async (id: number) => {
  await api.delete(`/presets/${id}?username=${username}`);
  ElMessage.success('预设已删除');
  fetchPresets();
};

const openEditPreset = (preset: any) => {
  editingPreset.value = { 
    ...preset,
    device_ids_array: preset.device_ids.split(',').map((id: string) => parseInt(id))
  };
  showEditPreset.value = true;
};

const handleUpdatePreset = async () => {
  if (!editingPreset.value.name || !editingPreset.value.device_ids_array.length) {
    return ElMessage.warning('请填写名称并至少选择一个设备');
  }
  loading.value = true;
  try {
    await api.put(`/presets/${editingPreset.value.id}?username=${username}`, {
      name: editingPreset.value.name,
      device_ids: editingPreset.value.device_ids_array.join(','),
      notes: editingPreset.value.notes
    });
    ElMessage.success('预设更新成功');
    showEditPreset.value = false;
    fetchPresets();
  } catch (err) {
    ElMessage.error('更新失败');
  } finally {
    loading.value = false;
  }
};

const stopGroup = async (group: any) => {
  ElMessageBox.confirm(`确定要结束该实验吗？(包含 ${group.devices.length} 台设备)`, '提示', {
    confirmButtonText: '确认结束',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
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
  return d.toLocaleString('zh-CN', { 
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' 
  });
};

const copyLink = () => {
  navigator.clipboard.writeText(shareLink.value);
  ElMessage.success('链接已复制');
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
    const idNum = parseInt(scanId);
    api.get('/devices').then(res => {
      const device = res.data.find((d: any) => d.id === idNum);
      if (device && device.status === 0) {
        selectedDevices.value = [device];
        ElMessage.info(`扫码选中: ${device.name}`);
      }
    });
  } else if (batchIds) {
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
  background-color: #f5f7fa;
  padding-bottom: 100px;
}

/* 顶部导航栏 */
.custom-header {
  background: #fff;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  position: sticky;
  top: 0;
  z-index: 100;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-name {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  letter-spacing: -0.5px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.add-btn {
  font-weight: 600;
}
.user-avatar {
  width: 36px;
  height: 36px;
  background: #ecf5ff;
  color: #409EFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  transition: all 0.2s;
}
.user-avatar:hover {
  background: #409EFF;
  color: #fff;
}

.main-content {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.admin-footer {
  text-align: center;
  margin-top: 40px;
  padding: 20px;
  border-top: 1px solid #ebeef5;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}
.search-input {
  width: 300px;
}

/* 现代设备卡片 */
.device-card-modern {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 24px;
  border: 2px solid transparent;
  cursor: pointer;
}
.device-card-modern:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}
.device-card-modern.is-selected {
  border-color: #67C23A;
  background: #f0f9eb;
}
.device-card-modern.is-disabled {
  opacity: 0.8;
  cursor: not-allowed;
  filter: grayscale(0.8);
}

.card-image-wrapper {
  height: 160px;
  position: relative;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
}
.device-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.no-img-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.status-idle { background: #67C23A; }
.status-busy { background: #F56C6C; }
.status-borrow { background: #E6A23C; }
.status-error { background: #909399; }

/* 照片采集区域 */
.photo-capture-area {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}
.preview-box {
  width: 100%;
  max-width: 300px;
  height: 200px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: #f8f9fa;
  transition: all 0.2s;
}
.preview-box:hover {
  border-color: #409EFF;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-placeholder {
  text-align: center;
  color: #909399;
}
.preview-placeholder p {
  margin-top: 8px;
  font-size: 14px;
}

.selection-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(103, 194, 58, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

.card-content {
  padding: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}
.device-name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}
.asset-code {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}
.card-meta {
  display: flex;
  gap: 12px;
  color: #606266;
  font-size: 13px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 实验管理样式 */
.experiments-container {
  padding: 0 10px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
.count-badge {
  background: #f56c6c;
  color: #fff;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  vertical-align: middle;
}
.count-badge.secondary {
  background: #409EFF;
}

.active-experiments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.experiment-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.05);
  border-left: 4px solid #F56C6C;
}
.exp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.time-info {
  display: flex;
  flex-direction: column;
}
.time-info .label {
  font-size: 12px;
  color: #909399;
}
.time-info .value {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.exp-divider {
  height: 1px;
  background: #ebeef5;
  margin-bottom: 15px;
}
.exp-device-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #409EFF;
}
.exp-device-item .code {
  color: #909399;
  font-size: 12px;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}
.preset-card-modern {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #ebeef5;
  transition: all 0.2s;
}
.preset-card-modern:hover {
  border-color: #409EFF;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}
.preset-icon {
  width: 40px;
  height: 40px;
  background: #ecf5ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409EFF;
}
.preset-info {
  flex: 1;
}
.preset-info h4 {
  margin: 0 0 4px 0;
  font-size: 15px;
  color: #303133;
}
.preset-info p {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

/* 底部浮动购物车 */
.floating-cart {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  width: 90%;
  max-width: 600px;
}
.cart-content {
  background: rgba(48, 49, 51, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 50px;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  color: #fff;
}
.cart-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.count {
  background: #67C23A;
  color: #fff;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 13px;
}
.device-preview {
  font-size: 13px;
  color: #dcdfe6;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cart-actions {
  display: flex;
  gap: 10px;
}
.start-btn {
  padding-left: 20px;
  padding-right: 20px;
}

.upload-btn-wrapper input[type=file] {
  font-size: 100px;
  position: absolute;
  left: 0;
  top: 0;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}
.upload-btn-wrapper {
  position: relative;
  overflow: hidden;
  display: inline-block;
  width: 100%;
}

/* 过渡动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translate(-50%, 100%);
  opacity: 0;
}
.scanner-dot {
  width: 100%;
  height: 2px;
  background: #409EFF;
  position: absolute;
  top: 50%;
  left: 0;
  box-shadow: 0 0 15px #409EFF;
  animation: scan-move 2s infinite ease-in-out;
}
@keyframes scan-move {
  0% { transform: translateY(-40px); opacity: 0; }
  50% { opacity: 1; }
  100% { transform: translateY(40px); opacity: 0; }
}
</style>
