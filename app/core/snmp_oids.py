"""
SNMP OID definitions for various vendors
"""

# LLDP MIB OIDs (IEEE 802.1AB)
LLDP_REM_TABLE = "1.0.8802.1.1.2.1.4.1"
LLDP_REM_CHASSIS_ID = "1.0.8802.1.1.2.1.4.1.1.5"
LLDP_REM_PORT_ID = "1.0.8802.1.1.2.1.4.1.1.7"
LLDP_REM_SYS_NAME = "1.0.8802.1.1.2.1.4.1.1.9"
LLDP_LOC_PORT_TABLE = "1.0.8802.1.1.2.1.3.7"

# CDP OIDs (Cisco)
CDP_CACHE_DEVICE_ID = "1.3.6.1.4.1.9.9.23.1.2.1.1.6"
CDP_CACHE_DEVICE_PORT = "1.3.6.1.4.1.9.9.23.1.2.1.1.7"
CDP_CACHE_PLATFORM = "1.3.6.1.4.1.9.9.23.1.2.1.1.8"
CDP_CACHE_ADDRESS = "1.3.6.1.4.1.9.9.23.1.2.1.1.4"

# Interface MIB OIDs
IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
IF_SPEED = "1.3.6.1.2.1.2.2.1.5"
IF_HIGH_SPEED = "1.3.6.1.2.1.31.1.1.1.15"
IF_HC_IN_OCTETS = "1.3.6.1.2.1.31.1.1.1.6"
IF_HC_OUT_OCTETS = "1.3.6.1.2.1.31.1.1.1.10"
IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"
IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7"

# System MIB OIDs
SYS_NAME = "1.3.6.1.2.1.1.5.0"
SYS_DESCR = "1.3.6.1.2.1.1.1.0"
SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
SYS_OBJECT_ID = "1.3.6.1.2.1.1.2.0"

# Vendor-specific CPU/Memory OIDs
VENDOR_OIDS = {
    "cisco_ios": {
        "cpu_5min": "1.3.6.1.4.1.9.9.109.1.1.1.1.8",
        "memory_used": "1.3.6.1.4.1.9.9.48.1.1.1.5",
        "memory_free": "1.3.6.1.4.1.9.9.48.1.1.1.6"
    },
    "cisco_nxos": {
        "cpu_5min": "1.3.6.1.4.1.9.9.109.1.1.1.1.8",
        "memory_used": "1.3.6.1.4.1.9.9.48.1.1.1.5",
        "memory_free": "1.3.6.1.4.1.9.9.48.1.1.1.6"
    },
    "fortinet": {
        "cpu": "1.3.6.1.4.1.12356.101.4.1.3.0",
        "memory": "1.3.6.1.4.1.12356.101.4.1.4.0"
    },
    "paloalto": {
        "cpu": "1.3.6.1.2.1.25.3.3.1.2",  # HOST-RESOURCES-MIB
        "memory_used": "1.3.6.1.2.1.25.2.3.1.6",
        "memory_size": "1.3.6.1.2.1.25.2.3.1.5"
    },
    "hp_aruba": {
        "cpu": "1.3.6.1.4.1.11.2.14.11.5.1.9.6.1.0",
        "memory": "1.3.6.1.4.1.11.2.14.11.5.1.1.2.1.1.1.5"
    },
    "ruckus": {
        "cpu": "1.3.6.1.4.1.25053.1.2.2.1.1.1.15.1.0",  # Ruckus CPU util
        "memory": "1.3.6.1.4.1.25053.1.2.2.1.1.1.15.2.0"  # Ruckus Memory util
    }
}

# Vendor detection patterns
VENDOR_PATTERNS = {
    "cisco ios": "cisco_ios",
    "cisco nx-os": "cisco_nxos",
    "cisco nexus": "cisco_nxos",
    "fortigate": "fortinet",
    "fortios": "fortinet",
    "palo alto": "paloalto",
    "pan-os": "paloalto",
    "procurve": "hp_aruba",
    "aruba": "hp_aruba",
    "hpe": "hp_aruba",
    "ruckus": "ruckus",
    "unleashed": "ruckus",
    "smartzone": "ruckus"
}


def detect_vendor(sys_descr: str) -> str:
    """Detect vendor from sysDescr"""
    if not sys_descr:
        return "unknown"
    
    sys_descr_lower = sys_descr.lower()
    
    for pattern, vendor in VENDOR_PATTERNS.items():
        if pattern in sys_descr_lower:
            return vendor
    
    return "unknown"
