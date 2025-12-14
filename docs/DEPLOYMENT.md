# DEV-lldp-topomon Ubuntu 部署指南

## 目錄

- [系統需求](#系統需求)
- [部署方式一：Docker Compose（建議）](#部署方式一docker-compose建議)
- [部署方式二：Native 安裝](#部署方式二native-安裝)
- [防火牆設定](#防火牆設定)
- [Systemd 服務設定](#systemd-服務設定)
- [Nginx 反向代理（可選）](#nginx-反向代理可選)
- [驗證部署](#驗證部署)
- [疑難排解](#疑難排解)

---

## 系統需求

| 項目 | 最低需求 | 建議配置 |
|------|----------|----------|
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB | 50 GB SSD |
| Python | 3.11+ | 3.11+ |
| PostgreSQL | 15+ | 15+ |
| Redis | 7+ | 7+ |

---

## 部署方式一：Docker Compose（建議）

### 1. 安裝 Docker 與 Docker Compose

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝必要套件
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 新增 Docker 官方 GPG 金鑰
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 新增 Docker 儲存庫
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安裝 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 將當前使用者加入 docker 群組
sudo usermod -aG docker $USER

# 啟用並啟動 Docker
sudo systemctl enable docker
sudo systemctl start docker

# 重新登入以套用群組變更
# 或執行: newgrp docker
```

### 2. 部署專案

```bash
# Clone 專案（或從其他來源取得）
cd /opt
sudo git clone https://github.com/nox913106/DEV-lldp-topomon.git
sudo chown -R $USER:$USER DEV-lldp-topomon
cd DEV-lldp-topomon

# 建立環境設定檔
cp .env.example .env

# 編輯環境變數（依需求修改）
nano .env
```

### 3. 設定環境變數

編輯 `.env` 檔案，修改以下關鍵設定：

```env
# 正式環境設定
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=your-random-secret-key-here

# 資料庫密碼（建議修改）
POSTGRES_PASSWORD=your-strong-password

# SNMP 設定
SNMP_DEFAULT_COMMUNITY=your-community-string
```

### 4. 啟動服務

```bash
# 建置並啟動所有容器
docker compose up -d

# 檢查容器狀態
docker compose ps

# 查看日誌
docker compose logs -f app
```

### 5. 驗證部署

```bash
# 確認所有服務都在運行
docker compose ps

# 測試 Web UI
curl http://localhost:8080/health

# 查看 API 文件
# 瀏覽器開啟: http://<your-server-ip>:8080/docs
```

---

## 部署方式二：Native 安裝

### 1. 安裝系統依賴

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 安裝建置工具
sudo apt install -y build-essential libpq-dev git
```

### 2. 安裝 PostgreSQL 15

```bash
# 新增 PostgreSQL 儲存庫
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# 安裝 PostgreSQL
sudo apt update
sudo apt install -y postgresql-15

# 啟動並啟用 PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 建立資料庫和使用者
sudo -u postgres psql << EOF
CREATE USER topomon WITH PASSWORD 'your-strong-password';
CREATE DATABASE topomon OWNER topomon;
GRANT ALL PRIVILEGES ON DATABASE topomon TO topomon;
EOF
```

### 3. 安裝 Redis 7

```bash
# 安裝 Redis
sudo apt install -y redis-server

# 編輯配置（可選：設定密碼）
sudo nano /etc/redis/redis.conf

# 啟動並啟用 Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 驗證 Redis
redis-cli ping
```

### 4. 部署應用程式

```bash
# 建立應用程式目錄
sudo mkdir -p /opt/topomon
sudo chown -R $USER:$USER /opt/topomon
cd /opt/topomon

# Clone 專案
git clone https://github.com/nox913106/DEV-lldp-topomon.git .

# 建立虛擬環境
python3.11 -m venv venv
source venv/bin/activate

# 安裝 Python 套件
pip install --upgrade pip
pip install -r requirements.txt

# 建立環境設定檔
cp .env.example .env
nano .env
```

### 5. 設定環境變數

編輯 `/opt/topomon/.env`：

```env
# 應用程式
APP_NAME=DEV-lldp-topomon
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=your-random-secret-key-here

# 資料庫（使用本地連線）
DATABASE_URL=postgresql+asyncpg://topomon:your-strong-password@localhost:5432/topomon

# Redis
REDIS_URL=redis://localhost:6379

# SNMP 設定
SNMP_DEFAULT_COMMUNITY=your-community-string
SNMP_TIMEOUT=5
SNMP_RETRIES=2

# Collector 設定
COLLECTOR_INTERVAL=300
COLLECTOR_CONCURRENT=20
```

---

## Systemd 服務設定

### 建立 Web 應用服務

```bash
sudo tee /etc/systemd/system/topomon-web.service << EOF
[Unit]
Description=LLDP Topology Monitor Web Service
After=network.target postgresql.service redis-server.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/topomon
Environment="PATH=/opt/topomon/venv/bin"
EnvironmentFile=/opt/topomon/.env
ExecStart=/opt/topomon/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 建立 Collector 服務

```bash
sudo tee /etc/systemd/system/topomon-collector.service << EOF
[Unit]
Description=LLDP Topology Monitor Collector Service
After=network.target postgresql.service redis-server.service topomon-web.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/topomon
Environment="PATH=/opt/topomon/venv/bin"
EnvironmentFile=/opt/topomon/.env
ExecStart=/opt/topomon/venv/bin/python -m app.collector
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 啟動服務

```bash
# 重新載入 systemd
sudo systemctl daemon-reload

# 啟用並啟動服務
sudo systemctl enable topomon-web topomon-collector
sudo systemctl start topomon-web topomon-collector

# 檢查服務狀態
sudo systemctl status topomon-web topomon-collector

# 查看日誌
sudo journalctl -u topomon-web -f
sudo journalctl -u topomon-collector -f
```

---

## 防火牆設定

```bash
# 安裝並啟用 UFW
sudo apt install -y ufw

# 允許 SSH（重要：避免被鎖住）
sudo ufw allow ssh

# 允許 Web 服務
sudo ufw allow 8080/tcp

# 如果使用 Nginx 反向代理
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 啟用防火牆
sudo ufw enable

# 確認規則
sudo ufw status
```

---

## Nginx 反向代理（可選）

### 安裝 Nginx

```bash
sudo apt install -y nginx
```

### 設定反向代理

```bash
sudo tee /etc/nginx/sites-available/topomon << EOF
server {
    listen 80;
    server_name your-domain.com;  # 替換為您的域名或 IP

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # 靜態檔案（可選優化）
    location /static/ {
        alias /opt/topomon/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 啟用站點
sudo ln -s /etc/nginx/sites-available/topomon /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 測試並重啟 Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### 設定 SSL（Let's Encrypt）

```bash
# 安裝 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 取得 SSL 憑證
sudo certbot --nginx -d your-domain.com

# 自動更新憑證
sudo systemctl enable certbot.timer
```

---

## 驗證部署

### 健康檢查

```bash
# 檢查 Web 服務
curl -s http://localhost:8080/health | jq

# 檢查資料庫連線
curl -s http://localhost:8080/api/v1/devices | jq

# 檢查所有服務狀態
sudo systemctl status topomon-web topomon-collector postgresql redis-server
```

### 預期輸出

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## 疑難排解

### 常見問題

#### 1. 資料庫連線失敗

```bash
# 檢查 PostgreSQL 狀態
sudo systemctl status postgresql

# 檢查連線
sudo -u postgres psql -c "SELECT 1;"

# 檢查 pg_hba.conf 設定
sudo nano /etc/postgresql/15/main/pg_hba.conf
# 確保有以下行：
# local   all   topomon   md5
# host    all   topomon   127.0.0.1/32   md5
```

#### 2. Redis 連線失敗

```bash
# 檢查 Redis 狀態
sudo systemctl status redis-server

# 測試連線
redis-cli ping
```

#### 3. Port 衝突

```bash
# 檢查 8080 port 使用情況
sudo lsof -i :8080

# 如需更換 port，修改 .env 或 docker-compose.yml
```

#### 4. 權限問題

```bash
# 修正目錄權限
sudo chown -R $USER:$USER /opt/topomon

# 確認虛擬環境權限
chmod -R 755 /opt/topomon/venv
```

#### 5. Docker 官方源連線失敗（網路限制）

如果遇到無法連接 `download.docker.com` 的問題：

**方案 A：使用 Ubuntu 官方倉庫（建議）**

```bash
# 使用 Ubuntu 官方倉庫的 docker.io 套件
sudo apt update
sudo apt install -y docker.io docker-compose-v2

# 啟用並啟動服務
sudo systemctl enable docker
sudo systemctl start docker

# 驗證安裝
docker --version
```

> **注意**：Ubuntu 官方倉庫的 Docker 版本可能較舊，但功能完整，適合內網環境。

**方案 B：使用鏡像源**

```bash
# 使用阿里雲鏡像（中國區域適用）
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

**方案 C：離線安裝**

1. 在可連網的電腦下載 Docker 安裝包：
   - 前往 https://download.docker.com/linux/ubuntu/dists/
   - 下載對應版本的 `.deb` 檔案

2. 使用 USB 或 SCP 傳輸到目標伺服器

3. 手動安裝：
```bash
sudo dpkg -i containerd.io_*.deb
sudo dpkg -i docker-ce-cli_*.deb
sudo dpkg -i docker-ce_*.deb
sudo dpkg -i docker-compose-plugin_*.deb
```

### 日誌位置

| 服務 | 日誌位置 |
|------|----------|
| Web 服務 | `sudo journalctl -u topomon-web` |
| Collector | `sudo journalctl -u topomon-collector` |
| PostgreSQL | `/var/log/postgresql/` |
| Redis | `/var/log/redis/` |
| Nginx | `/var/log/nginx/` |
| Docker | `docker compose logs` |

---

## 更新應用程式

### Docker Compose 方式

```bash
cd /opt/DEV-lldp-topomon

# 拉取最新程式碼
git pull

# 重建並重啟容器
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Native 方式

```bash
cd /opt/topomon

# 拉取最新程式碼
git pull

# 更新套件
source venv/bin/activate
pip install -r requirements.txt

# 重啟服務
sudo systemctl restart topomon-web topomon-collector
```

---

## 備份與還原

### 備份資料庫

```bash
# Docker 方式
docker compose exec db pg_dump -U topomon topomon > backup_$(date +%Y%m%d).sql

# Native 方式
pg_dump -U topomon -h localhost topomon > backup_$(date +%Y%m%d).sql
```

### 還原資料庫

```bash
# Docker 方式
cat backup.sql | docker compose exec -T db psql -U topomon topomon

# Native 方式
psql -U topomon -h localhost topomon < backup.sql
```
