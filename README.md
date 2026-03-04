# LabTrack

轻量级实验室资产与效率管理工具。

## 快速启动

### 方式一：Docker 一键部署 (推荐)
直接使用 GitHub Container Registry (GHCR) 的预构建镜像部署：

1. **下载 `docker-compose.yml`** (或直接克隆本仓库)
2. **启动容器**:
   ```bash
   docker compose up -d
   ```
   *注意：默认使用 `ghcr.io/water2004/labtrack-frontend:latest` 和 `ghcr.io/water2004/labtrack-backend:latest`。*

### 方式二：本地构建部署
1. 进入项目根目录。
2. 执行: `docker compose up -d --build`

### 方式三：手动分步启动
#### 1. 后端 (FastAPI)
1. 进入 `backend` 目录。
2. 安装依赖: `pip install -r requirements.txt`
3. 启动服务: `python main.py`
   - 服务运行在: `http://localhost:8000`
   - 管理员默认密码: `LabAdmin2024` (可通过环境变量 `ADMIN_PASSWORD` 修改)

#### 2. 前端 (Vue 3)
1. 进入 `frontend` 目录。
2. 安装依赖: `npm install`
3. 启动开发服务器: `npm run dev`
   - 访问: `http://localhost:5173`

## 使用说明
1. **管理员登录**: 访问 `/admin-login`，输入密码。
2. **添加用户**: 在后台添加可以在前台登录的用户名。
3. **添加设备**: 在后台录入设备，并上传图片。
4. **用户登录**: 首页输入用户名即可。
5. **开始实验**: 点击设备卡片上的 `+` 号，点击右下角“开始实验”。
6. **扫码支持**: 访问 `http://localhost:5173/?id=[设备ID]` 可直接选中该设备。
