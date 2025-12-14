#!/bin/bash
#
# DEV-lldp-topomon 快速部署腳本 (Ubuntu 22.04)
# 使用方式: sudo bash deploy.sh [docker|native]
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函數：輸出訊息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 檢查是否為 root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此腳本需要 root 權限執行，請使用 sudo"
    fi
}

# 檢查 Ubuntu 版本
check_ubuntu() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        error "此腳本僅支援 Ubuntu 系統"
    fi
    info "系統檢查通過: $(lsb_release -ds)"
}

# 安裝 Docker
install_docker() {
    info "安裝 Docker..."
    
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    
    # 嘗試使用 Docker 官方源，如果失敗則使用 Ubuntu 官方倉庫
    info "嘗試從 Docker 官方源安裝..."
    
    # 設定超時時間（30秒）
    TIMEOUT=30
    
    if timeout $TIMEOUT curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.gpg 2>/dev/null; then
        info "成功取得 Docker GPG 金鑰"
        gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg < /tmp/docker.gpg
        rm -f /tmp/docker.gpg
        
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        warn "無法連接 Docker 官方源，改用 Ubuntu 官方倉庫..."
        warn "（Ubuntu 官方倉庫的 Docker 版本可能較舊，但功能完整）"
        
        # 使用 Ubuntu 官方倉庫的 docker.io
        apt-get install -y docker.io docker-compose-v2
        
        # 如果 docker-compose-v2 不可用，嘗試安裝 docker-compose
        if ! command -v docker compose &> /dev/null; then
            apt-get install -y docker-compose || true
        fi
    fi
    
    systemctl enable docker
    systemctl start docker
    
    # 驗證安裝
    if docker --version &> /dev/null; then
        info "Docker 安裝完成: $(docker --version)"
    else
        error "Docker 安裝失敗"
    fi
}

# 安裝 PostgreSQL
install_postgresql() {
    info "安裝 PostgreSQL 15..."
    
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
    
    apt-get update
    apt-get install -y postgresql-15
    
    systemctl enable postgresql
    systemctl start postgresql
    
    info "PostgreSQL 安裝完成"
}

# 安裝 Redis
install_redis() {
    info "安裝 Redis..."
    
    apt-get install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
    
    info "Redis 安裝完成"
}

# 安裝 Python 3.11
install_python() {
    info "安裝 Python 3.11..."
    
    add-apt-repository ppa:deadsnakes/ppa -y
    apt-get update
    apt-get install -y python3.11 python3.11-venv python3.11-dev build-essential libpq-dev
    
    info "Python 3.11 安裝完成"
}

# Docker 部署
deploy_docker() {
    info "開始 Docker 部署..."
    
    # 安裝 Docker
    if ! command -v docker &> /dev/null; then
        install_docker
    else
        info "Docker 已安裝"
    fi
    
    # 準備專案目錄
    PROJECT_DIR="/opt/DEV-lldp-topomon"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        warn "專案目錄已存在，將更新..."
        cd "$PROJECT_DIR"
        git pull || true
    else
        info "Clone 專案..."
        git clone https://github.com/nox913106/DEV-lldp-topomon.git "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    # 建立環境設定
    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        # 產生隨機密鑰
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "s/change-this-to-random-string/$SECRET_KEY/" .env
        info "已建立 .env 檔案，請檢查並修改設定"
    fi
    
    # 啟動服務
    info "啟動 Docker 服務..."
    docker compose up -d
    
    # 等待服務啟動
    info "等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    docker compose ps
    
    info "Docker 部署完成！"
    info "Web UI: http://$(hostname -I | awk '{print $1}'):8080"
}

# Native 部署
deploy_native() {
    info "開始 Native 部署..."
    
    # 系統更新
    apt-get update && apt-get upgrade -y
    
    # 安裝依賴
    install_python
    install_postgresql
    install_redis
    
    # 準備專案目錄
    PROJECT_DIR="/opt/topomon"
    DEPLOY_USER="${SUDO_USER:-$USER}"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        warn "專案目錄已存在，將更新..."
    else
        mkdir -p "$PROJECT_DIR"
    fi
    
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$PROJECT_DIR"
    
    # Clone 專案
    cd "$PROJECT_DIR"
    if [[ -d ".git" ]]; then
        sudo -u "$DEPLOY_USER" git pull || true
    else
        sudo -u "$DEPLOY_USER" git clone https://github.com/nox913106/DEV-lldp-topomon.git .
    fi
    
    # 建立虛擬環境
    info "建立 Python 虛擬環境..."
    sudo -u "$DEPLOY_USER" python3.11 -m venv venv
    sudo -u "$DEPLOY_USER" venv/bin/pip install --upgrade pip
    sudo -u "$DEPLOY_USER" venv/bin/pip install -r requirements.txt
    
    # 建立環境設定
    if [[ ! -f ".env" ]]; then
        sudo -u "$DEPLOY_USER" cp .env.example .env
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "s/change-this-to-random-string/$SECRET_KEY/" .env
        # 更新為本地資料庫連線
        sed -i "s|postgresql://topomon:password@db:5432/topomon|postgresql+asyncpg://topomon:topomon@localhost:5432/topomon|" .env
        sed -i "s|redis://redis:6379|redis://localhost:6379|" .env
    fi
    
    # 建立資料庫
    info "設定 PostgreSQL 資料庫..."
    sudo -u postgres psql -c "CREATE USER topomon WITH PASSWORD 'topomon';" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE topomon OWNER topomon;" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE topomon TO topomon;" 2>/dev/null || true
    
    # 建立 Systemd 服務
    info "建立 Systemd 服務..."
    
    cat > /etc/systemd/system/topomon-web.service << EOF
[Unit]
Description=LLDP Topology Monitor Web Service
After=network.target postgresql.service redis-server.service

[Service]
Type=exec
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    cat > /etc/systemd/system/topomon-collector.service << EOF
[Unit]
Description=LLDP Topology Monitor Collector Service
After=network.target postgresql.service redis-server.service topomon-web.service

[Service]
Type=exec
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python -m app.collector
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 啟動服務
    systemctl daemon-reload
    systemctl enable topomon-web topomon-collector
    systemctl start topomon-web topomon-collector
    
    # 等待服務啟動
    sleep 5
    
    # 檢查服務狀態
    systemctl status topomon-web --no-pager
    systemctl status topomon-collector --no-pager
    
    info "Native 部署完成！"
    info "Web UI: http://$(hostname -I | awk '{print $1}'):8080"
}

# 主程式
main() {
    check_root
    check_ubuntu
    
    DEPLOY_MODE="${1:-docker}"
    
    case "$DEPLOY_MODE" in
        docker)
            deploy_docker
            ;;
        native)
            deploy_native
            ;;
        *)
            error "未知的部署模式: $DEPLOY_MODE\n使用方式: $0 [docker|native]"
            ;;
    esac
    
    info "部署完成！"
    echo ""
    echo "========================================="
    echo "  DEV-lldp-topomon 部署成功"
    echo "========================================="
    echo ""
    echo "  Web UI: http://$(hostname -I | awk '{print $1}'):8080"
    echo "  API 文件: http://$(hostname -I | awk '{print $1}'):8080/docs"
    echo ""
    echo "  請修改 .env 檔案中的 SNMP Community 設定"
    echo "  詳細說明請參閱 docs/DEPLOYMENT.md"
    echo ""
}

main "$@"
