/**
 * Internationalization (i18n) support
 * Supports: English (default), Traditional Chinese, Simplified Chinese
 */

const i18n = {
    currentLang: 'en',

    translations: {
        en: {
            // Navigation
            topology: 'Topology',
            devices: 'Devices',
            alerts: 'Alerts',
            groups: 'Groups',
            settings: 'Settings',

            // Topology controls
            overview: 'Overview',
            fullMap: 'Full Map',
            groupView: 'Group View',
            selectGroup: 'Select Group...',
            refresh: 'Refresh',
            fit: 'Fit',
            lastUpdate: 'Last update',

            // Status
            online: 'Online',
            offline: 'Offline',
            managed: 'Managed',
            unknown: 'Unknown',
            normal: 'Normal',
            elevated: 'Elevated',
            warning: 'Warning',
            critical: 'Critical',

            // Device types
            core: 'Core Switch',
            distribution: 'Distribution',
            access: 'Access Switch',
            router: 'Router',
            firewall: 'Firewall',
            ap: 'Access Point',

            // Details panel
            details: 'Details',
            deviceInfo: 'Device Info',
            ipAddress: 'IP Address',
            type: 'Type',
            vendor: 'Vendor',
            status: 'Status',
            metrics: 'Metrics',
            cpu: 'CPU',
            memory: 'Memory',

            // Link details
            linkDetails: 'Link Details',
            connection: 'Connection',
            from: 'From',
            to: 'To',
            bandwidth: 'Bandwidth',
            total: 'Total',
            inUtilization: 'In Utilization',
            outUtilization: 'Out Utilization',
            portDetails: 'Port Details',

            // Alerts
            activeAlerts: 'Active Alerts',
            noActiveAlerts: 'No active alerts',

            // Settings
            snmpSettings: 'SNMP Configuration',
            alertProfiles: 'Alert Profiles',
            logExport: 'Log Export',
            notifications: 'Notifications',

            // Common
            save: 'Save',
            cancel: 'Cancel',
            delete: 'Delete',
            edit: 'Edit',
            add: 'Add',
            close: 'Close',
            loading: 'Loading...',
            error: 'Error',
            success: 'Success'
        },

        'zh-TW': {
            // Navigation
            topology: '拓撲圖',
            devices: '設備',
            alerts: '告警',
            groups: '群組',
            settings: '設定',

            // Topology controls
            overview: '總覽',
            fullMap: '完整地圖',
            groupView: '群組視圖',
            selectGroup: '選擇群組...',
            refresh: '重新整理',
            fit: '適配',
            lastUpdate: '最後更新',

            // Status
            online: '線上',
            offline: '離線',
            managed: '受管理',
            unknown: '未知',
            normal: '正常',
            elevated: '偏高',
            warning: '警告',
            critical: '嚴重',

            // Device types
            core: '核心交換機',
            distribution: '分發交換機',
            access: '接入交換機',
            router: '路由器',
            firewall: '防火牆',
            ap: '無線基地台',

            // Details panel
            details: '詳細資訊',
            deviceInfo: '設備資訊',
            ipAddress: 'IP 位址',
            type: '類型',
            vendor: '廠商',
            status: '狀態',
            metrics: '指標',
            cpu: 'CPU',
            memory: '記憶體',

            // Link details
            linkDetails: '連結詳情',
            connection: '連接',
            from: '來源',
            to: '目標',
            bandwidth: '頻寬',
            total: '總計',
            inUtilization: '輸入使用率',
            outUtilization: '輸出使用率',
            portDetails: '埠詳情',

            // Alerts
            activeAlerts: '活躍告警',
            noActiveAlerts: '無告警',

            // Settings
            snmpSettings: 'SNMP 設定',
            alertProfiles: '告警設定檔',
            logExport: '日誌匯出',
            notifications: '通知',

            // Common
            save: '儲存',
            cancel: '取消',
            delete: '刪除',
            edit: '編輯',
            add: '新增',
            close: '關閉',
            loading: '載入中...',
            error: '錯誤',
            success: '成功'
        },

        'zh-CN': {
            // Navigation
            topology: '拓扑图',
            devices: '设备',
            alerts: '告警',
            groups: '群组',
            settings: '设置',

            // Topology controls
            overview: '概览',
            fullMap: '完整地图',
            groupView: '群组视图',
            selectGroup: '选择群组...',
            refresh: '刷新',
            fit: '适配',
            lastUpdate: '最后更新',

            // Status
            online: '在线',
            offline: '离线',
            managed: '受管理',
            unknown: '未知',
            normal: '正常',
            elevated: '偏高',
            warning: '警告',
            critical: '严重',

            // Device types
            core: '核心交换机',
            distribution: '分发交换机',
            access: '接入交换机',
            router: '路由器',
            firewall: '防火墙',
            ap: '无线访问点',

            // Details panel
            details: '详细信息',
            deviceInfo: '设备信息',
            ipAddress: 'IP 地址',
            type: '类型',
            vendor: '厂商',
            status: '状态',
            metrics: '指标',
            cpu: 'CPU',
            memory: '内存',

            // Link details
            linkDetails: '链接详情',
            connection: '连接',
            from: '来源',
            to: '目标',
            bandwidth: '带宽',
            total: '总计',
            inUtilization: '输入利用率',
            outUtilization: '输出利用率',
            portDetails: '端口详情',

            // Alerts
            activeAlerts: '活跃告警',
            noActiveAlerts: '无告警',

            // Settings
            snmpSettings: 'SNMP 配置',
            alertProfiles: '告警配置文件',
            logExport: '日志导出',
            notifications: '通知',

            // Common
            save: '保存',
            cancel: '取消',
            delete: '删除',
            edit: '编辑',
            add: '添加',
            close: '关闭',
            loading: '加载中...',
            error: '错误',
            success: '成功'
        }
    },

    init() {
        // Load saved language or use browser default
        const saved = localStorage.getItem('language');
        if (saved && this.translations[saved]) {
            this.currentLang = saved;
        } else {
            // Detect browser language
            const browserLang = navigator.language || navigator.userLanguage;
            if (browserLang.startsWith('zh-TW') || browserLang.startsWith('zh-Hant')) {
                this.currentLang = 'zh-TW';
            } else if (browserLang.startsWith('zh')) {
                this.currentLang = 'zh-CN';
            } else {
                this.currentLang = 'en';
            }
        }
        this.applyTranslations();
    },

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('language', lang);
            this.applyTranslations();
        }
    },

    t(key) {
        return this.translations[this.currentLang]?.[key] ||
            this.translations['en'][key] ||
            key;
    },

    applyTranslations() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });

        // Update placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });

        // Update titles
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.t(key);
        });
    }
};

// Export for use
window.i18n = i18n;
