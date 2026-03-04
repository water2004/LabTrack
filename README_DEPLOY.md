# LabTrack 部署指南

本项目采用 Docker Compose 进行容器化部署。

## 部署要求
- Docker
- Docker Compose

## 部署步骤

1. **创建数据目录**
   在项目根目录下创建 `data` 目录（用于持久化数据）：
   ```bash
   mkdir data
   ```

2. **一键启动**

   **方式 A：使用本地构建 (克隆仓库后执行)**
   ```bash
   docker compose up -d --build
   ```
   *注：构建配置中已开启 `network: host`，以避开容器内网络下载依赖包慢或失败的问题。*

   **方式 B：直接使用 GHCR 镜像部署 (无需克隆完整仓库，仅需 `docker-compose.ghcr.yml`)**
   ```bash
   # 如果没有克隆仓库，可以单独下载该文件
   docker compose -f docker-compose.ghcr.yml up -d
   ```

3. **访问地址**
   - 前端页面：`http://localhost`
   - 后端文档：`http://localhost/api/docs`

## 关键说明
- **数据映射**：主机的 `./data` 目录映射到容器内的 `/app/data`，包含 SQLite 数据库和上传的图片。
- **端口配置**：前端默认占用主机 `80` 端口。如需修改，请调整 `docker-compose.yml` 中的 `ports` 部分。
- **管理员密码**：默认管理员密码为 `LabAdmin2024`，可通过环境变量 `ADMIN_PASSWORD` 修改。
