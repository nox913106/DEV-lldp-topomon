# DEV-lldp-topomon

LLDP/CDP Topology Monitor - 網路拓撲監控系統

## 專案簡介

基於 LLDP/CDP 協定的網路拓撲自動發現與監控系統，提供乾淨的視覺化拓撲圖和完整的告警機制。

### 核心功能

- 🔍 **自動發現**：透過 LLDP/CDP 自動探索網路設備
- 🗺️ **拓撲視覺化**：乾淨的網路拓撲圖（合併重複 link）
- 📊 **流量監控**：即時顯示 link 頻寬使用率
- 🚨 **智慧告警**：可自訂閾值的告警系統
- 📝 **Log 整合**：支援輸出至 Elasticsearch/Graylog

### 支援設備

- Cisco (IOS, NX-OS)
- HP ProCurve
- Aruba
- Fortinet FortiGate
- Palo Alto Networks

## 系統需求

- Ubuntu 22.04 LTS
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (建議)

## 快速開始

```bash
# Clone 專案
git clone https://github.com/nox913106/DEV-lldp-topomon.git
cd DEV-lldp-topomon

# 使用 Docker Compose 啟動
docker-compose up -d

# 訪問 Web UI
open http://localhost:8080
```

## 文件

- [系統設計文件 (SDD)](docs/SDD.md)
- [API 文件](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [設定說明](docs/CONFIGURATION.md)

## 授權

MIT License
