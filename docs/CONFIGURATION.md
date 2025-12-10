# DEV-lldp-topomon 設定說明

## 1. 環境變數

複製 `.env.example` 為 `.env` 並修改：

```bash
cp .env.example .env
```

### 基本設定

```env
# 應用程式
APP_NAME=DEV-lldp-topomon
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# 資料庫
DATABASE_URL=postgresql://topomon:password@localhost:5432/topomon

# Redis
REDIS_URL=redis://localhost:6379

# SNMP 預設設定
SNMP_DEFAULT_COMMUNITY=public
SNMP_TIMEOUT=5
SNMP_RETRIES=2

# Collector 設定
COLLECTOR_INTERVAL=300
COLLECTOR_CONCURRENT=20

# Log 輸出 (可選)
LOG_EXPORT_ENABLED=false
LOG_EXPORT_TYPE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
```

---

## 2. 設定檔

### config.yaml

```yaml
app:
  name: "DEV-lldp-topomon"
  debug: false
  log_level: "INFO"

snmp:
  default_community: "public"
  timeout: 5
  retries: 2

collector:
  interval_seconds: 300
  concurrent_connections: 20
  
discovery:
  enabled: true
  auto_add_neighbors: true

log_export:
  enabled: false
  type: "elasticsearch"
  elasticsearch:
    url: "http://localhost:9200"
    index_prefix: "topomon-"
  graylog:
    host: "localhost"
    port: 12201
    protocol: "udp"
```

---

## 3. SNMP Community 管理

可以在 Web UI 或設定檔中設定多組 SNMP community：

```yaml
snmp:
  communities:
    - name: "public"
      priority: 1
    - name: "private"
      priority: 2
    - name: "custom_community"
      priority: 3
```

發現設備時會依優先序嘗試連線。

---

## 4. 廠商自動偵測

系統會根據 sysDescr 自動判斷設備廠商：

| 關鍵字 | 廠商 |
|--------|------|
| `Cisco` | Cisco |
| `ProCurve`, `Aruba` | HP/Aruba |
| `FortiGate` | Fortinet |
| `Palo Alto` | Palo Alto |

可自訂額外規則：

```yaml
vendor_detection:
  rules:
    - pattern: ".*Custom-OS.*"
      vendor: "custom"
      cpu_oid: "1.3.6.1.4.1.xxx"
      memory_oid: "1.3.6.1.4.1.xxx"
```
