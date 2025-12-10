# DEV-lldp-topomon 系統設計文件 (SDD)

**版本**：1.0  
**日期**：2025-12-10  
**狀態**：Draft

---

## 1. 文件概述

### 1.1 目的

本文件描述 DEV-lldp-topomon 系統的軟體設計，包含系統架構、模組設計、資料庫結構、API 規格等技術細節。

### 1.2 範圍

本系統為一個基於 LLDP/CDP 協定的網路拓撲監控系統，主要功能包括：
- 網路設備自動發現
- 拓撲圖視覺化
- 流量監控
- 告警管理

### 1.3 設計目標

| 目標 | 說明 |
|------|------|
| **簡潔拓撲** | 每對設備只顯示一條合併的 link |
| **即時監控** | 顯示 link 即時流量使用率 |
| **彈性告警** | 可自訂閾值 Profile 套用不同場景 |
| **可擴展性** | 支援 600+ 設備規模 |
| **Log 整合** | 支援輸出至 Elasticsearch/Graylog |

### 1.4 設計約束

- **作業系統**：Ubuntu 22.04 LTS
- **SNMP 版本**：v2c
- **支援廠商**：Cisco, HP, Aruba, FortiGate, Palo Alto
- **獨立部署**：不依賴 LibreNMS

---

## 2. 系統架構

### 2.1 整體架構圖

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                              │
│                    Web Browser (D3.js Topology)                     │
└─────────────────────────────────────────────────────────────────────┘
                                   │ HTTP/WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Application Layer                           │
│     Nginx  │  FastAPI (REST API)  │  WebSocket (Real-time)          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Service Layer                               │
│  SNMP Collector │ Topology Engine │ Alert Engine │ Discovery       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                 │
│       PostgreSQL    │    Redis    │    Elasticsearch                │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Network Devices                              │
│        Cisco │ HP │ Aruba │ FortiGate │ Palo Alto (SNMP v2c)        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模組說明

| 模組 | 功能 | 技術 |
|------|------|------|
| **Web Server** | 靜態檔案服務、反向代理 | Nginx |
| **API Server** | RESTful API 服務 | FastAPI |
| **SNMP Collector** | SNMP 資料收集 | pysnmp |
| **Topology Engine** | 拓撲圖建構與 Link 合併 | NetworkX |
| **Alert Engine** | 告警判斷與通知 | 自訂實作 |
| **Discovery Service** | 設備自動發現 | 自訂實作 |
| **Log Exporter** | 日誌輸出至外部系統 | elasticsearch-py |

---

## 3. SNMP Collector 模組

### 3.1 收集的 OIDs

**LLDP-MIB**
```
lldpRemSysName       1.0.8802.1.1.2.1.4.1.1.9   # 遠端系統名稱
lldpRemPortId        1.0.8802.1.1.2.1.4.1.1.7   # 遠端 Port ID
lldpRemChassisId     1.0.8802.1.1.2.1.4.1.1.5   # 遠端 Chassis ID
```

**CDP (Cisco)**
```
cdpCacheDeviceId     1.3.6.1.4.1.9.9.23.1.2.1.1.6
cdpCacheDevicePort   1.3.6.1.4.1.9.9.23.1.2.1.1.7
```

**IF-MIB (Interface)**
```
ifDescr              1.3.6.1.2.1.2.2.1.2
ifHighSpeed          1.3.6.1.2.1.31.1.1.1.15
ifHCInOctets         1.3.6.1.2.1.31.1.1.1.6
ifHCOutOctets        1.3.6.1.2.1.31.1.1.1.10
```

### 3.2 廠商特定 OIDs

| 廠商 | CPU OID | Memory OID |
|------|---------|------------|
| Cisco IOS | 1.3.6.1.4.1.9.9.109.1.1.1.1.8 | 1.3.6.1.4.1.9.9.48.1.1.1.5/6 |
| FortiGate | 1.3.6.1.4.1.12356.101.4.1.3 | 1.3.6.1.4.1.12356.101.4.1.4 |
| Palo Alto | 1.3.6.1.2.1.25.3.3.1.2 | 1.3.6.1.2.1.25.2.3.1.6 |
| HP/Aruba | 1.3.6.1.4.1.11.2.14.11.5.1.9.6.1 | vendor specific |

### 3.3 輪詢策略

```
600 台設備 / 5 分鐘間隔
使用 async + 20 並行連線
預估總輪詢時間 < 2 分鐘
```

---

## 4. Topology Engine 模組

### 4.1 Link 合併邏輯

```
輸入:
  DeviceA:Gi0/1 <-> DeviceB:Gi0/1  (1Gbps)
  DeviceA:Gi0/2 <-> DeviceB:Gi0/2  (1Gbps)
  
輸出:
  DeviceA ══════════════ DeviceB
        (2x1G = 2Gbps, 45%)
```

### 4.2 排除規則

```yaml
exclude_rules:
  - type: hostname_pattern
    pattern: "^AP-.*"           # 排除 AP 設備
  - type: hostname_pattern
    pattern: "^SEP.*"           # 排除 IP Phone
  - type: device_pair
    device_a: "Core-1"
    device_b: "Mgmt-SW"         # 排除特定連線
```

---

## 5. Alert Engine 模組

### 5.1 告警類型

| 告警類型 | 觸發條件 | 復歸條件 |
|----------|----------|----------|
| `device_offline` | SNMP 連續 N 次失敗 | SNMP 恢復 |
| `device_online` | SNMP 復歸 | - |
| `link_high_utilization` | 使用率 > 閾值 | 使用率 < 復歸值 |
| `cpu_high` | CPU > 閾值 | CPU < 復歸值 |
| `memory_high` | Memory > 閾值 | Memory < 復歸值 |
| `new_device_discovered` | 新設備發現 | - |

### 5.2 Alert Profile 結構

```yaml
profiles:
  - name: "Core Device"
    thresholds:
      link_utilization: {warning: 60, critical: 80, recovery_buffer: 10}
      cpu: {warning: 70, critical: 85}
      memory: {warning: 75, critical: 90}
      device_offline_retry: 2
      
  - name: "Access Device"
    thresholds:
      link_utilization: {warning: 80, critical: 95}
      cpu: {warning: 85, critical: 95}
      memory: {warning: 85, critical: 95}
      device_offline_retry: 3
```

### 5.3 告警狀態機

```
NORMAL → (value > warning) → WARNING
WARNING → (value > critical) → CRITICAL
CRITICAL → (value < recovery) → NORMAL + 復歸通知
```

---

## 6. 資料庫設計

詳見 [SDD-Database.md](SDD-Database.md)

---

## 7. API 設計

詳見 [SDD-API.md](SDD-API.md)

---

## 8. 前端設計

### 8.1 頁面結構

| 路徑 | 功能 |
|------|------|
| `/` | 首頁 - 拓撲圖 |
| `/devices` | 設備管理列表 |
| `/alerts` | 告警管理 |
| `/profiles` | Profile 管理 |
| `/settings` | 系統設定 |

### 8.2 Link 顏色編碼

| 使用率 | 顏色 | 狀態 |
|--------|------|------|
| 0-50% | 🟢 綠色 | Normal |
| 50-70% | 🟡 黃色 | Elevated |
| 70-90% | 🟠 橙色 | Warning |
| 90-100% | 🔴 紅色 | Critical |

---

## 9. 部署架構

### 9.1 Docker Compose

```yaml
services:
  app:
    build: .
    ports: ["8080:8080"]
    depends_on: [db, redis]
    
  collector:
    build: .
    command: python -m app.collector
    
  db:
    image: postgres:15-alpine
    
  redis:
    image: redis:7-alpine
```

### 9.2 系統需求

| 資源 | 最低需求 | 建議配置 |
|------|----------|----------|
| CPU | 2 cores | 4 cores |
| Memory | 4 GB | 8 GB |
| Disk | 20 GB | 50 GB |

---

## 10. 專案目錄結構

```
DEV-lldp-topomon/
├── app/
│   ├── api/           # API 路由
│   ├── core/          # 核心服務
│   ├── models/        # 資料模型
│   ├── schemas/       # Pydantic Schemas
│   └── db/            # 資料庫
├── static/            # 前端靜態檔案
├── docs/              # 文件
├── tests/             # 測試
└── docker-compose.yml
```

---

## 11. 開發時程

| 階段 | 時間 | 交付項目 |
|------|------|----------|
| Phase 1 | Week 1-2 | 基礎架構、SNMP Collector |
| Phase 2 | Week 3 | 拓撲視覺化、流量監控 |
| Phase 3 | Week 4 | 告警系統、Profile 管理 |
| Phase 4 | Week 5 | Web UI 完整功能 |
| Phase 5 | Week 6 | 測試、文件、部署 |
