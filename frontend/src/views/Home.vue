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
              <el-radio-button value="all">全部设备</el-radio-button>
              <el-radio-button value="mine">我负责的</el-radio-button>
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
                  <img v-if="device.image_path" :src="`${baseURL}${device.image_path}`" class="device-img" />
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
        <el-link type="info" underline="never" @click="$router.push('/admin-login')">
          <el-icon><Setting /></el-icon> 管理后台
        </el-link>
        <div class="footer-info">
          <el-link href="https://github.com/water2004/LabTrack" target="_blank" type="info" underline="never">
            Powered by LabTrack
          </el-link>
          <span class="version-badge">v1.1.0</span>
        </div>
      </div>
    </main>

    <!-- 录入设备弹窗 -->
    <el-dialog v-model="showAddDevice" title="录入新设备" :width="dialogWidth" center>
      <div class="photo-capture-area">
        <div class="preview-box" @click="(($refs.fileInputAdd as any).click())">
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
        <div class="preview-box" @click="(($refs.fileInputEdit as any).click())">
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

    <!-- 条形码扫描（隐藏 input） -->
    <input 
      type="file" 
      ref="scannerFileInput" 
      hidden 
      accept="image/*" 
      capture="environment" 
      @change="handleScannerFile" 
    />

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

    <!-- 裁剪框选对话框 -->
    <el-dialog 
      v-model="showCropDialog" 
      title="框选条形码区域" 
      width="90%" 
      style="max-width: 500px" 
      center 
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="crop-container">
        <div class="crop-wrapper" ref="cropWrapper">
          <img :src="cropSourceUrl" ref="cropImg" class="crop-image" @load="initCropBox" />
          <div 
            class="selection-box" 
            :style="selectionStyle"
            @mousedown.stop="e => startDrag(e.clientX, e.clientY)"
            @touchstart.stop="e => e.touches && e.touches[0] && startDrag(e.touches[0].clientX, e.touches[0].clientY)"
          >
            <div class="selection-handle top-left" 
              @mousedown.stop="e => startDrag(e.clientX, e.clientY, 'resize', 'top-left')"
              @touchstart.stop="e => e.touches && e.touches[0] && startDrag(e.touches[0].clientX, e.touches[0].clientY, 'resize', 'top-left')"></div>
            <div class="selection-handle top-right"
              @mousedown.stop="e => startDrag(e.clientX, e.clientY, 'resize', 'top-right')"
              @touchstart.stop="e => e.touches && e.touches[0] && startDrag(e.touches[0].clientX, e.touches[0].clientY, 'resize', 'top-right')"></div>
            <div class="selection-handle bottom-left"
              @mousedown.stop="e => startDrag(e.clientX, e.clientY, 'resize', 'bottom-left')"
              @touchstart.stop="e => e.touches && e.touches[0] && startDrag(e.touches[0].clientX, e.touches[0].clientY, 'resize', 'bottom-left')"></div>
            <div class="selection-handle bottom-right"
              @mousedown.stop="e => startDrag(e.clientX, e.clientY, 'resize', 'bottom-right')"
              @touchstart.stop="e => e.touches && e.touches[0] && startDrag(e.touches[0].clientX, e.touches[0].clientY, 'resize', 'bottom-right')"></div>
            <div class="scan-line-anim"></div>
          </div>
        </div>
        <p class="crop-tip">手指拖动方框，对准条形码</p>
        
        <!-- 调试预览：显示经过锐化处理后的图像 -->
        <div v-if="debugImageUrl" class="debug-preview">
          <p class="debug-label">引擎识别视角 (锐化+增强):</p>
          <img :src="debugImageUrl" class="debug-img" />
        </div>
      </div>
      <template #footer>
        <el-button @click="showCropDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCropAndScan" :loading="scanning">开始识别</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api, { baseURL } from '../api';
import Quagga from '@ericblade/quagga2';
import { 
  Search, Check, VideoPlay, Plus, Picture, Location, User, 
  Right, CircleCheckFilled, Collection, Delete, ElementPlus,
  Edit, Setting, Camera, FullScreen
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

const windowWidth = ref(window.innerWidth);
onMounted(() => {
  window.addEventListener('resize', () => {
    windowWidth.value = window.innerWidth;
  });
});

const dialogWidth = computed(() => {
  return windowWidth.value < 768 ? '95%' : '500px';
});

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
const debugImageUrl = ref('');

// 扫码与裁剪逻辑
const showCropDialog = ref(false);
const cropSourceUrl = ref('');
const cropImg = ref<HTMLImageElement | null>(null);
const cropWrapper = ref<HTMLDivElement | null>(null);
const scanning = ref(false);

const selection = ref({ x: 50, y: 100, w: 200, h: 80 }); // 初始选择框位置
const selectionStyle = computed(() => ({
  left: `${selection.value.x}px`,
  top: `${selection.value.y}px`,
  width: `${selection.value.w}px`,
  height: `${selection.value.h}px`
}));

let isDragging = false;
let dragMode = 'move'; // 'move' 或 'resize'
let resizeDir = ''; // 'top-left', 'top-right', etc.
let startX = 0;
let startY = 0;
let startBox = { x: 0, y: 0, w: 0, h: 0 };

const startDrag = (clientX: number, clientY: number, mode: 'move' | 'resize' = 'move', dir: string = '') => {
  isDragging = true;
  dragMode = mode;
  resizeDir = dir;
  startX = clientX;
  startY = clientY;
  startBox = { ...selection.value };
  
  window.addEventListener('mousemove', handleGlobalMove);
  window.addEventListener('mouseup', stopDrag);
  window.addEventListener('touchmove', handleGlobalTouchMove, { passive: false });
  window.addEventListener('touchend', stopDrag);
};

const handleGlobalMove = (e: MouseEvent) => {
  if (!isDragging) return;
  updateSelection(e.clientX, e.clientY);
};

const handleGlobalTouchMove = (e: TouchEvent) => {
  if (!isDragging) return;
  e.preventDefault();
  const touch = e.touches[0];
  if (touch) {
    updateSelection(touch.clientX, touch.clientY);
  }
};

const updateSelection = (clientX: number, clientY: number) => {
  const dx = clientX - startX;
  const dy = clientY - startY;
  const container = cropWrapper.value;
  if (!container) return;

  if (dragMode === 'move') {
    let newX = startBox.x + dx;
    let newY = startBox.y + dy;
    newX = Math.max(0, Math.min(newX, container.clientWidth - selection.value.w));
    newY = Math.max(0, Math.min(newY, container.clientHeight - selection.value.h));
    selection.value.x = newX;
    selection.value.y = newY;
  } else if (dragMode === 'resize') {
    const minSize = 40;
    let { x, y, w, h } = { ...startBox };

    if (resizeDir.includes('right')) {
      w = Math.max(minSize, Math.min(startBox.w + dx, container.clientWidth - startBox.x));
    }
    if (resizeDir.includes('bottom')) {
      h = Math.max(minSize, Math.min(startBox.h + dy, container.clientHeight - startBox.y));
    }
    if (resizeDir.includes('left')) {
      const maxDx = startBox.w - minSize;
      const validDx = Math.max(-startBox.x, Math.min(dx, maxDx));
      x = startBox.x + validDx;
      w = startBox.w - validDx;
    }
    if (resizeDir.includes('top')) {
      const maxDy = startBox.h - minSize;
      const validDy = Math.max(-startBox.y, Math.min(dy, maxDy));
      y = startBox.y + validDy;
      h = startBox.h - validDy;
    }

    selection.value = { x, y, w, h };
  }
};

const stopDrag = () => {
  isDragging = false;
  window.removeEventListener('mousemove', handleGlobalMove);
  window.removeEventListener('mouseup', stopDrag);
  window.removeEventListener('touchmove', handleGlobalTouchMove);
  window.removeEventListener('touchend', stopDrag);
};

const initCropBox = () => {
  const container = cropWrapper.value;
  if (container) {
    selection.value = {
      x: (container.clientWidth - 250) / 2,
      y: (container.clientHeight - 100) / 2,
      w: 250,
      h: 100
    };
  }
};

// 图像锐化处理函数 (卷积矩阵)
const sharpen = (ctx: CanvasRenderingContext2D, w: number, h: number, amount: number = 0.5) => {
  const kernel = [
    0, -1, 0,
    -1, 5, -1,
    0, -1, 0
  ];
  const imageData = ctx.getImageData(0, 0, w, h);
  const data = imageData.data;
  const buffer = new Uint8ClampedArray(data);
  
  for (let y = 1; y < h - 1; y++) {
    for (let xc = 1; xc < w - 1; xc++) {
      const p = (y * w + xc) * 4;
      for (let c = 0; c < 3; c++) {
        let res = 0;
        for (let iy = -1; iy <= 1; iy++) {
          for (let ix = -1; ix <= 1; ix++) {
            const ip = ((y + iy) * w + (xc + ix)) * 4;
            // 将非空断言移动到索引之后，以断言访问结果不为 undefined
            res += buffer[ip + c]! * kernel[(iy + 1) * 3 + (ix + 1)]!;
          }
        }
        data[p + c] = buffer[p + c]! + (res - buffer[p + c]!) * amount;
      }
    }
  }
  ctx.putImageData(imageData, 0, 0);
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-';
  const d = new Date(timeStr);
  return d.toLocaleString('zh-CN', { 
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' 
  });
};

const scannerFileInput = ref<HTMLInputElement | null>(null);
const scannerTarget = ref<'add' | 'edit'>('add');

const openScanner = (target: 'add' | 'edit') => {
  scannerTarget.value = target;
  if (scannerFileInput.value) {
    scannerFileInput.value.click();
  }
};

const handleScannerFile = async (event: any) => {
  const file = event.target.files[0];
  if (!file) return;
  
  cropSourceUrl.value = URL.createObjectURL(file);
  showCropDialog.value = true;
};

const confirmCropAndScan = async () => {
  if (!cropImg.value || !cropWrapper.value) return;
  scanning.value = true;

  try {
    const img = cropImg.value;
    const scaleX = img.naturalWidth / img.clientWidth;
    const scaleY = img.naturalHeight / img.clientHeight;
    
    const padding = 0.15;
    let cropX = (selection.value.x - selection.value.w * padding / 2) * scaleX;
    let cropY = (selection.value.y - selection.value.h * padding / 2) * scaleY;
    let cropW = selection.value.w * (1 + padding) * scaleX;
    let cropH = selection.value.h * (1 + padding) * scaleY;

    cropX = Math.max(0, cropX);
    cropY = Math.max(0, cropY);
    cropW = Math.min(img.naturalWidth - cropX, cropW);
    cropH = Math.min(img.naturalHeight - cropY, cropH);

    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = (cropH / cropW) * 1200;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas Context Error');
    
    // 2. 增强图像对比度并应用锐化（重新加入灰度）
    ctx.filter = 'contrast(1.4) brightness(1.1) grayscale(1)';
    ctx.drawImage(img, cropX, cropY, cropW, cropH, 0, 0, canvas.width, canvas.height);

    // 减弱锐化强度，防止产生干扰伪影
    sharpen(ctx, canvas.width, canvas.height, 0.4);


    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    debugImageUrl.value = dataUrl; // 关键修复：将处理后的图像传给 UI 显示

    const result: any = await new Promise((resolve, reject) => {
      Quagga.decodeSingle({
        src: dataUrl,
        numOfWorkers: 0,
        decoder: {
          readers: [
            "code_128_reader", "ean_reader", "ean_8_reader", 
            "code_39_reader", "codabar_reader", "upc_reader"
          ]
        },
        locate: true
      }, (result) => {
        if (result && result.codeResult) {
          resolve(result);
        } else {
          reject(new Error("未发现有效条码"));
        }
      });
    });

    const decodedText = result.codeResult.code;
    
    if (scannerTarget.value === 'add') {
      newDevice.value.asset_code = decodedText;
    } else {
      editingDevice.value.asset_code = decodedText;
    }
    
    ElMessage.success('解析成功: ' + decodedText);
    showCropDialog.value = false;
  } catch (err) {
    ElMessage.error('该区域未识别到条码。建议：调整框选范围，包含完整的条码线条及少量留白');
  } finally {
    scanning.value = false;
    if (scannerFileInput.value) scannerFileInput.value.value = '';
  }
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
  pendingNotes.value = '';
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

const openEdit = (device: any) => {
  editingDevice.value = { ...device };
  previewUrl.value = device.image_path ? `${baseURL}${device.image_path}` : '';
  selectedFile.value = null;
  fetchUsers();
  showEditDevice.value = true;
};

const handleUpdate = async () => {
  if (!editingDevice.value.name) return;
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
    formData.append('asset_code', editingDevice.value.asset_code || '');
    formData.append('status', editingDevice.value.status.toString());
    formData.append('username', username || '');
    if (selectedFile.value) formData.append('image', selectedFile.value);
    
    await api.put(`/devices/${editingDevice.value.id}`, formData);
    ElMessage.success('更新成功');
    showEditDevice.value = false;
    fetchDevices();
  } catch (err: any) {
    ElMessage.error('更新失败');
  } finally {
    loading.value = false;
  }
};

const addDevice = async () => {
  if (!newDevice.value.name) return ElMessage.warning('请填写设备名称');
  loading.value = true;
  const formData = new FormData();
  formData.append('name', newDevice.value.name);
  formData.append('asset_code', newDevice.value.asset_code || '');
  formData.append('location', newDevice.value.location || '');
  formData.append('manager', username || '');
  if (selectedFile.value) formData.append('image', selectedFile.value);

  try {
    await api.post('/admin/devices', formData);
    ElMessage.success('设备录入成功');
    showAddDevice.value = false;
    newDevice.value = { name: '', asset_code: '', location: '', manager: username };
    selectedFile.value = null;
    fetchDevices();
  } catch (err: any) {
    ElMessage.error('录入失败');
  } finally {
    loading.value = false;
  }
};

const startExperiment = async () => {
  ElMessageBox.prompt('请输入本次实验备注 (必填)', '开始实验', {
    confirmButtonText: '立即开始',
    cancelButtonText: '取消',
    inputValue: pendingNotes.value,
    inputPattern: /\S+/,
    inputErrorMessage: '备注不能为空',
  }).then(async (data: any) => {
    try {
      const ids = selectedDevices.value.map(d => d.id);
      await api.post('/experiment/start', { 
        device_ids: ids,
        notes: data.value || ''
      }, { params: { username } });
      
      const baseUrl = window.location.origin + window.location.pathname;
      shareLink.value = `${baseUrl}?ids=${ids.join(',')}`;
      selectedDevices.value = [];
      showLinkDialog.value = true;
      fetchDevices();
      fetchActiveGroups();
    } catch (err: any) {
      ElMessage.error('启动失败');
    }
  });
};

const promptSavePreset = () => {
  ElMessageBox.prompt('请输入预设名称', '保存预设', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  }).then(async (data: any) => {
    if (!data.value) return;
    const ids = selectedDevices.value.map(d => d.id).join(',');
    await api.post('/presets', { name: data.value, device_ids: ids }, { params: { username } });
    ElMessage.success('预设已保存');
    fetchPresets();
  });
};

const applyPreset = (preset: any) => {
  const ids = preset.device_ids.split(',').map((id: string) => parseInt(id));
  const available = devices.value.filter(d => ids.includes(d.id) && d.status === 0);
  if (available.length === 0) return ElMessage.warning('无可用设备');
  selectedDevices.value = available;
  pendingNotes.value = preset.notes || '';
  activeTab.value = 'devices';
};

const deletePreset = async (id: number) => {
  await api.delete(`/presets/${id}`, { params: { username } });
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
  if (!editingPreset.value.name || !editingPreset.value.device_ids_array.length) return;
  loading.value = true;
  try {
    await api.put(`/presets/${editingPreset.value.id}`, {
      name: editingPreset.value.name,
      device_ids: editingPreset.value.device_ids_array.join(','),
      notes: editingPreset.value.notes
    }, { params: { username } });
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
  ElMessageBox.confirm(`确定要结束该实验吗？`, '提示', {
    confirmButtonText: '确认结束',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const ids = group.devices.map((d: any) => d.id);
      await api.post('/experiment/stop', { device_ids: ids }, { params: { username } });
      ElMessage.success('实验已结束');
      fetchDevices();
      fetchActiveGroups();
    } catch (err) {
      ElMessage.error('结束失败');
    }
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
    api.get('/devices').then(res => {
      const device = res.data.find((d: any) => d.id === parseInt(scanId));
      if (device && device.status === 0) selectedDevices.value = [device];
    });
  } else if (batchIds) {
    const ids = batchIds.split(',').map(id => parseInt(id));
    api.get('/devices').then(res => {
      selectedDevices.value = res.data.filter((d: any) => ids.includes(d.id) && d.status === 0);
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
.logo-area { display: flex; align-items: center; gap: 10px; }
.logo-icon {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.brand-name { font-size: 20px; font-weight: 700; color: #303133; }
.header-actions { display: flex; align-items: center; gap: 16px; }
.user-avatar {
  width: 36px; height: 36px; background: #ecf5ff; color: #409EFF;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: bold; cursor: pointer; border: 2px solid #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
.main-content { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
.admin-footer {
  text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #ebeef5;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.footer-info { display: flex; align-items: center; gap: 12px; opacity: 0.7; }
.version-badge {
  font-size: 11px; color: #a8abb2; border: 1px solid #e4e7ed; padding: 1px 6px;
  border-radius: 4px; background: #fff; transition: all 0.3s;
}
.version-badge:hover { color: #409EFF; border-color: #c6e2ff; background: #ecf5ff; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 16px; }
.device-card-modern {
  background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); margin-bottom: 24px; border: 2px solid transparent; cursor: pointer;
}
.device-card-modern:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
.device-card-modern.is-selected { border-color: #67C23A; background: #f0f9eb; }
.device-card-modern.is-disabled { opacity: 0.8; cursor: not-allowed; filter: grayscale(0.8); }
.card-image-wrapper { height: 160px; position: relative; background: #f8f9fa; display: flex; align-items: center; justify-content: center; }
.device-img { width: 100%; height: 100%; object-fit: cover; }
.status-badge {
  position: absolute; top: 12px; right: 12px; padding: 4px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600; color: #fff; backdrop-filter: blur(4px);
}
.status-idle { background: #67C23A; }
.status-busy { background: #F56C6C; }
.status-borrow { background: #E6A23C; }
.status-error { background: #909399; }
.selection-indicator {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(103, 194, 58, 0.2);
  display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px);
}
.card-content { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.device-name { margin: 0; font-size: 16px; font-weight: 700; color: #303133; }
.asset-code { font-size: 12px; color: #909399; background: #f4f4f5; padding: 2px 6px; border-radius: 4px; }
.card-meta { display: flex; gap: 12px; color: #606266; font-size: 13px; }
.photo-capture-area { margin-bottom: 20px; display: flex; justify-content: center; }
.preview-box {
  width: 100%; max-width: 300px; height: 200px; border: 2px dashed #dcdfe6; border-radius: 12px;
  overflow: hidden; display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.active-experiments-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.experiment-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.05); border-left: 4px solid #F56C6C; }
.presets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
.preset-card-modern { background: #fff; border-radius: 12px; padding: 16px; display: flex; align-items: center; gap: 16px; border: 1px solid #ebeef5; }
.floating-cart { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 1000; width: 90%; max-width: 600px; }
.cart-content { background: rgba(48, 49, 51, 0.95); border-radius: 50px; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; color: #fff; }
.crop-container { display: flex; flex-direction: column; align-items: center; gap: 15px; }
.crop-wrapper { position: relative; width: 100%; max-height: 60vh; background: #000; overflow: hidden; border-radius: 8px; touch-action: none; }
.crop-image { display: block; width: 100%; height: auto; }
.selection-box { position: absolute; border: 2px solid #409EFF; box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5); z-index: 10; }
.selection-handle {
  position: absolute;
  width: 15px;
  height: 15px;
  background: #409EFF;
  border-radius: 2px;
}
@media (max-width: 768px) {
  .selection-handle {
    width: 24px;
    height: 24px;
    border-radius: 4px;
  }
  .top-left { top: -10px; left: -10px; }
  .top-right { top: -10px; right: -10px; }
  .bottom-left { bottom: -10px; left: -10px; }
  .bottom-right { bottom: -10px; right: -10px; }

  .cart-content {
    padding: 10px 16px;
  }
  .device-preview {
    display: none; /* 手机端隐藏已选名称预览以节省空间 */
  }
  .custom-header {
    padding: 0 12px;
  }
  .brand-name {
    display: none; /* 手机端隐藏标题文字，只留图标 */
  }
}
.top-left { top: -5px; left: -5px; }
 .top-right { top: -5px; right: -5px; }
.bottom-left { bottom: -5px; left: -5px; } .bottom-right { bottom: -5px; right: -5px; }
.scan-line-anim { width: 100%; height: 2px; background: rgba(64, 158, 255, 0.8); position: absolute; animation: scan-vertical 2s infinite ease-in-out; }
@keyframes scan-vertical { 0% { transform: translateY(-400%); opacity: 0; } 50% { opacity: 1; } 100% { transform: translateY(400%); opacity: 0; } }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s; }
.slide-up-enter-from, .slide-up-leave-to { transform: translate(-50%, 100%); opacity: 0; }

/* 调试预览样式 */
.debug-preview {
  margin-top: 15px;
  padding: 10px;
  background: #f0f2f5;
  border-radius: 8px;
  border: 1px dashed #dcdfe6;
}
.debug-label {
  font-size: 12px;
  color: #606266;
  margin: 0 0 8px 0;
  font-weight: bold;
}
.debug-img {
  width: 100%;
  max-height: 100px;
  object-fit: contain;
  display: block;
  background: #fff;
}
</style>
