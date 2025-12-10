# DEV-lldp-topomon 資料庫設計文件

## 1. ER Diagram

```
devices ─────────────┬──► alert_profiles
    │                │
    │ 1:N            │
    ▼                │
raw_links            │
    │                │
    │ Merge          │
    ▼                │
merged_links ◄───────┤
    │                │
    ▼                ▼
alerts ────────► alert_history
```

---

## 2. Table Schema

### 2.1 devices

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET NOT NULL,
    vendor VARCHAR(100),
    device_type VARCHAR(50),
    snmp_community VARCHAR(255) NOT NULL,
    alert_profile_id INTEGER REFERENCES alert_profiles(id),
    status VARCHAR(50) DEFAULT 'unknown',
    cpu_percent FLOAT,
    memory_percent FLOAT,
    uptime_seconds BIGINT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_devices_status ON devices(status);
```

### 2.2 alert_profiles

```sql
CREATE TABLE alert_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    thresholds JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**thresholds JSONB 範例：**
```json
{
  "link_utilization": {"warning": 70, "critical": 90, "recovery_buffer": 10},
  "cpu": {"warning": 80, "critical": 95},
  "memory": {"warning": 85, "critical": 95},
  "device_offline_retry": 3
}
```

### 2.3 raw_links

```sql
CREATE TABLE raw_links (
    id SERIAL PRIMARY KEY,
    local_device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    local_port VARCHAR(100),
    local_port_index INTEGER,
    remote_hostname VARCHAR(255),
    remote_port VARCHAR(100),
    protocol VARCHAR(10),  -- lldp, cdp
    discovered_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    UNIQUE(local_device_id, local_port, remote_hostname, remote_port)
);
```

### 2.4 merged_links

```sql
CREATE TABLE merged_links (
    id SERIAL PRIMARY KEY,
    device_a_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    device_b_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    total_bandwidth_mbps INTEGER,
    current_in_bps BIGINT,
    current_out_bps BIGINT,
    utilization_in_percent FLOAT,
    utilization_out_percent FLOAT,
    port_details JSONB,
    is_excluded BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(device_a_id, device_b_id)
);
```

**port_details JSONB 範例：**
```json
[
  {"local_port": "Gi0/1", "remote_port": "Gi0/24", "bandwidth_mbps": 1000, "in_bps": 450000000},
  {"local_port": "Gi0/2", "remote_port": "Gi0/25", "bandwidth_mbps": 1000, "in_bps": 320000000}
]
```

### 2.5 exclude_rules

```sql
CREATE TABLE exclude_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(50),  -- hostname_pattern, port_pattern, device_pair
    pattern VARCHAR(255),
    device_a_id INTEGER REFERENCES devices(id),
    device_b_id INTEGER REFERENCES devices(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.6 alerts

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    link_id INTEGER REFERENCES merged_links(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    current_value FLOAT,
    threshold_value FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMP DEFAULT NOW(),
    recovered_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100)
);

CREATE INDEX idx_alerts_active ON alerts(is_active) WHERE is_active = TRUE;
```

### 2.7 alert_history

```sql
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    event_type VARCHAR(50),  -- triggered, escalated, recovered, acknowledged
    event_time TIMESTAMP DEFAULT NOW(),
    details JSONB
);
```

### 2.8 system_config

```sql
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. 初始資料

```sql
-- 預設 Alert Profiles
INSERT INTO alert_profiles (name, description, thresholds, is_default) VALUES
('Core Device', '核心設備 - 嚴格閾值', 
 '{"link_utilization": {"warning": 60, "critical": 80, "recovery_buffer": 10}, 
   "cpu": {"warning": 70, "critical": 85, "recovery_buffer": 10}, 
   "memory": {"warning": 75, "critical": 90, "recovery_buffer": 10}, 
   "device_offline_retry": 2}', false),

('Distribution Device', '匯聚層設備', 
 '{"link_utilization": {"warning": 70, "critical": 85, "recovery_buffer": 10}, 
   "cpu": {"warning": 75, "critical": 90, "recovery_buffer": 10}, 
   "memory": {"warning": 80, "critical": 92, "recovery_buffer": 10}, 
   "device_offline_retry": 3}', false),

('Access Device', '接入層設備', 
 '{"link_utilization": {"warning": 80, "critical": 95, "recovery_buffer": 10}, 
   "cpu": {"warning": 85, "critical": 95, "recovery_buffer": 10}, 
   "memory": {"warning": 85, "critical": 95, "recovery_buffer": 10}, 
   "device_offline_retry": 3}', true);
```
