# DEV-lldp-topomon API 設計文件

## 1. API 總覽

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/devices` | GET, POST | 設備管理 |
| `/api/v1/devices/{id}` | GET, PUT, DELETE | 單一設備操作 |
| `/api/v1/topology` | GET | 取得拓撲資料 |
| `/api/v1/topology/exclude-rules` | GET, POST, DELETE | 排除規則 |
| `/api/v1/alerts` | GET | 告警列表 |
| `/api/v1/alerts/active` | GET | 活躍告警 |
| `/api/v1/alerts/{id}/acknowledge` | POST | 確認告警 |
| `/api/v1/profiles` | GET, POST | Profile 管理 |
| `/api/v1/profiles/{id}` | GET, PUT, DELETE | 單一 Profile |
| `/api/v1/discovery/start` | POST | 啟動發現 |
| `/api/v1/discovery/status` | GET | 發現狀態 |

---

## 2. 設備 API

### GET /api/v1/devices

列出所有設備

**Response:**
```json
{
  "devices": [
    {
      "id": 1,
      "hostname": "Core-1",
      "ip_address": "10.0.0.1",
      "vendor": "cisco",
      "device_type": "switch",
      "status": "online",
      "cpu_percent": 45.2,
      "memory_percent": 68.5,
      "alert_profile": {"id": 1, "name": "Core Device"},
      "last_seen": "2025-12-10T23:50:00+08:00"
    }
  ],
  "total": 1
}
```

### POST /api/v1/devices

新增設備

**Request:**
```json
{
  "hostname": "Core-1",
  "ip_address": "10.0.0.1",
  "snmp_community": "public",
  "alert_profile_id": 1,
  "auto_discover": true
}
```

---

## 3. 拓撲 API

### GET /api/v1/topology

取得拓撲資料（用於前端 D3.js）

**Response:**
```json
{
  "nodes": [
    {
      "id": "1",
      "hostname": "Core-1",
      "ip_address": "10.0.0.1",
      "device_type": "switch",
      "vendor": "cisco",
      "status": "online",
      "cpu_percent": 45.2,
      "memory_percent": 68.5,
      "alert_count": 1
    }
  ],
  "links": [
    {
      "id": "1",
      "source": "1",
      "target": "2",
      "total_bandwidth_mbps": 2000,
      "utilization_in_percent": 45.5,
      "utilization_out_percent": 32.1,
      "status": "normal",
      "port_details": [
        {"local": "Gi0/1", "remote": "Gi0/1", "bandwidth": 1000},
        {"local": "Gi0/2", "remote": "Gi0/2", "bandwidth": 1000}
      ]
    }
  ],
  "last_updated": "2025-12-10T23:50:00+08:00"
}
```

### POST /api/v1/topology/exclude-rules

新增排除規則

**Request:**
```json
{
  "rule_type": "hostname_pattern",
  "pattern": "^AP-.*"
}
```

或

```json
{
  "rule_type": "device_pair",
  "device_a_id": 1,
  "device_b_id": 5
}
```

---

## 4. 告警 API

### GET /api/v1/alerts/active

取得活躍告警

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "alert_type": "link_high_utilization",
      "severity": "warning",
      "device": {"id": 1, "hostname": "Core-1"},
      "link": {"id": 1, "source": "Core-1", "target": "Dist-1"},
      "message": "Link utilization 78.5% exceeds warning threshold 70%",
      "current_value": 78.5,
      "threshold_value": 70,
      "triggered_at": "2025-12-10T23:45:00+08:00",
      "duration_minutes": 5
    }
  ],
  "total": 1
}
```

### POST /api/v1/alerts/{id}/acknowledge

確認告警

**Request:**
```json
{
  "acknowledged_by": "admin"
}
```

---

## 5. Profile API

### GET /api/v1/profiles

列出所有 Profile

**Response:**
```json
{
  "profiles": [
    {
      "id": 1,
      "name": "Core Device",
      "description": "核心設備 - 嚴格閾值",
      "thresholds": {
        "link_utilization": {"warning": 60, "critical": 80, "recovery_buffer": 10},
        "cpu": {"warning": 70, "critical": 85, "recovery_buffer": 10},
        "memory": {"warning": 75, "critical": 90, "recovery_buffer": 10}
      },
      "is_default": false,
      "device_count": 5
    }
  ]
}
```

### POST /api/v1/profiles

新增 Profile

**Request:**
```json
{
  "name": "Custom Profile",
  "description": "自訂閾值",
  "thresholds": {
    "link_utilization": {"warning": 75, "critical": 90, "recovery_buffer": 10},
    "cpu": {"warning": 80, "critical": 95, "recovery_buffer": 10},
    "memory": {"warning": 80, "critical": 95, "recovery_buffer": 10},
    "device_offline_retry": 3
  }
}
```

---

## 6. 發現 API

### POST /api/v1/discovery/start

啟動設備發現

**Request:**
```json
{
  "seed_device_id": 1
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "started",
  "message": "Discovery started from device Core-1"
}
```

### GET /api/v1/discovery/status

查詢發現狀態

**Response:**
```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": {
    "discovered": 45,
    "pending": 12,
    "failed": 2
  },
  "started_at": "2025-12-10T23:50:00+08:00"
}
```

---

## 7. WebSocket API

### /ws/topology

即時拓撲更新

**Message Format:**
```json
{
  "type": "topology_update",
  "data": {
    "links": [
      {"id": "1", "utilization_in_percent": 48.2}
    ]
  }
}
```

### /ws/alerts

即時告警推送

**Message Format:**
```json
{
  "type": "new_alert",
  "data": {
    "id": 5,
    "alert_type": "device_offline",
    "severity": "critical",
    "device": {"hostname": "Acc-3"},
    "message": "Device offline"
  }
}
```
