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
            info: 'Info',

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
            deviceInformation: 'Device Information',
            ipAddress: 'IP Address',
            type: 'Type',
            vendor: 'Vendor',
            status: 'Status',
            metrics: 'Metrics',
            cpu: 'CPU',
            memory: 'Memory',
            model: 'Model',
            firmware: 'Firmware',
            lastSeen: 'Last Seen',
            hostname: 'Hostname',
            actions: 'Actions',
            upstreamDevices: 'Upstream Devices',
            downstreamDevices: 'Downstream Devices',

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

            // Alerts page
            activeAlerts: 'Active Alerts',
            noActiveAlerts: 'No active alerts',
            resolvedToday: 'Resolved Today',
            active: 'Active',
            all: 'All',
            acknowledgeAll: 'Acknowledge All',
            acknowledge: 'Acknowledge',
            recentActivity: 'Recent Activity',
            triggered: 'TRIGGERED',
            acknowledged: 'Ack\'d',
            acknowledgeReason: 'Acknowledge Reason',
            enterReason: 'Enter reason for acknowledgment...',
            reasonRequired: 'Please enter a reason',
            highCpu: 'High CPU',
            highMemory: 'High Memory',
            deviceOffline: 'Device Offline',
            linkHighUtilization: 'Link High Utilization',

            // Groups page
            newGroup: '+ New',
            editGroup: 'Edit Group',
            groupName: 'Name',
            description: 'Description',
            parentGroup: 'Parent Group',
            noneTopLevel: 'None (Top Level)',
            color: 'Color',
            selectAGroup: 'Select a Group',
            unassigned: 'Unassigned',
            noDevicesInGroup: 'Select a group to view its devices',
            moveSelectedTo: 'Move selected to...',
            move: 'Move',
            removeFromGroup: 'Remove from Group',

            // Settings page
            systemOverview: 'System Overview',
            totalDevices: 'Total Devices',
            totalLinks: 'Total Links',
            snmpConfiguration: 'SNMP Configuration',
            defaultCommunity: 'Default Community String',
            pollInterval: 'Poll Interval (seconds)',
            snmpTimeout: 'SNMP Timeout (seconds)',
            snmpRetries: 'SNMP Retries',
            saveSnmpSettings: 'Save SNMP Settings',
            alertProfiles: 'Alert Profiles',
            newProfile: '+ New Profile',
            logExport: 'Log Export',
            enableLogExport: 'Enable Log Export',
            exportType: 'Export Type',
            testConnection: 'Test Connection',
            notifications: 'Notifications',
            browserNotifications: 'Browser Notifications',
            soundAlerts: 'Sound Alerts',

            // Appearance settings
            appearance: 'Appearance',
            language: 'Language',
            theme: 'Theme',

            // SNMP subnet restriction
            allowedSubnets: 'Allowed Subnets',
            allowedSubnetsLabel: 'Target IP must be within the following subnets',
            enforceSubnetRestriction: 'Enable Subnet Restriction',
            cidrHelpText: 'One CIDR per line, leave empty for no restriction',
            subnetRestrictionHelp: 'When enabled, SNMP testing and device discovery only work for IPs within allowed subnets',

            // SNMP Testing Tools
            snmpTestingTools: 'SNMP Testing Tools',
            snmpConnectionTest: 'SNMP Connection Test',
            targetIp: 'Target IP',
            communityString: 'Community String',
            selectOid: 'Select OID',
            customOid: 'Custom OID',
            testResult: 'Test Result',
            manualDiscovery: 'Manual Device Discovery',
            startIp: 'Start IP',
            recursiveDiscovery: 'Recursive Discovery (Discover LLDP Neighbors)',
            recursiveDiscoveryHelp: 'When enabled, automatically discovers all neighbors of discovered devices',
            startDiscovery: 'Start Discovery',
            discoveryResult: 'Discovery Result',
            discoveryIp: 'IP Address',
            discoveryCommunity: 'Community String',
            oid: 'OID',
            oidOptional: 'OID (Optional)',
            sysDescr: 'sysDescr - System Description',
            sysName: 'sysName - Hostname',
            sysUpTime: 'sysUpTime - Uptime',
            lldpNeighbors: 'lldpRemTable - LLDP Neighbors',
            customOidOption: 'Custom OID...',

            // Dynamic messages
            enterTargetIp: 'Please enter target IP',
            enterStartIp: 'Please enter start IP',
            testing: 'Testing...',
            discovering: 'Discovering...',
            discoveryComplete: 'Discovery Complete',
            discoveredDevices: 'Discovered {count} devices, added {added} new',
            discoveryFailed: 'Discovery Failed',
            testSuccess: 'Test Successful',
            testFailed: 'Test Failed',
            settingsSaved: 'SNMP Settings Saved',
            ipNotInSubnets: '❌ IP {ip} is not in allowed subnets\n\nAllowed subnets: {subnets}',
            notConfigured: '(Not Configured)',
            newDevice: 'New',
            alreadyExists: 'Exists',

            // Alert detail modal
            device: 'Device',
            message: 'Message',
            timeline: 'Timeline',
            triggeredAt: 'Triggered',
            affectedDownstreamDevices: 'Affected Downstream Devices',
            devicesAffected: 'devices affected',
            causedBy: 'Caused By (Root Cause)',
            offlineUpstreamFailure: 'This device is offline because of upstream failure',
            viewRootCauseAlert: 'View Root Cause Alert →',
            acknowledgeHistory: 'Acknowledge History',

            // Common
            save: 'Save',
            cancel: 'Cancel',
            delete: 'Delete',
            edit: 'Edit',
            add: 'Add',
            close: 'Close',
            loading: 'Loading...',
            error: 'Error',
            success: 'Success',
            confirm: 'Confirm',
            viewFullDetails: 'View Full Details',
            viewInTopology: 'View in Topology',
            addDevice: '+ Add Device',
            searchHostnameOrIp: 'Search hostname or IP...',
            allStatus: 'All Status',
            allVendors: 'All Vendors',
            perPage: '/ page',
            showAll: 'Show All',
            recovered: 'RECOVERED',

            // Device Modal
            autoDetect: 'Auto Detect',
            deviceType: 'Device Type',
            snmpCommunity: 'SNMP Community',
            alertProfile: 'Alert Profile',
            autoDiscoverNeighbors: 'Auto-discover neighbors',
            default: 'Default',
            accessPoint: 'Access Point',
            editDevice: 'Edit Device',

            // Alerts page
            acknowledge: 'Acknowledge',
            acknowledgeAll: 'Acknowledge All',
            acknowledgeAlert: 'Acknowledge Alert',
            addNote: 'Add Note',
            acked: 'Ack\'d',
            ackHistory: 'Acknowledge History',
            noAckHistory: 'No acknowledge history',
            enterReason: 'Please enter reason:',
            reasonRequired: 'Reason is required',
            noDetails: 'No details',
            noAlerts: 'No alerts! Everything is running smoothly.',
            resolvedToday: 'Resolved Today',
            activeAlerts: 'Active Alerts',
            all: 'All',
            recentActivity: 'Recent Activity',
            triggered: 'TRIGGERED',
            noRecentActivity: 'No recent activity',

            // Suppress notifications
            suppressNotifications: 'Suppress Notifications',
            customDuration: 'Custom Duration',
            untilResolved: 'Until Resolved',
            noSuppress: 'No Suppress',
            minutes: 'Minutes',
            hours: 'Hours',
            days: 'Days',

            // History management
            noHistory: 'No history',
            noReason: 'No reason',
            edit: 'Edit',
            delete: 'Delete',
            deletedBy: 'Deleted by',
            until: 'Until',
            notificationsSuppressed: 'Notifications Suppressed',
            resumeNotifications: 'Resume Notifications',
            confirmUnsuppress: 'Resume notifications for this alert?',
            editReasonPrompt: 'Enter new reason:',
            deleteReasonPrompt: 'Enter deletion reason:',
            confirmRestoreNotifications: 'Restore notifications after deletion?',
            addNote: 'Add Note',
            enterNotePrompt: 'Enter new note (will be added to history):',
            errorLoadingHistory: 'Error loading history'
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
            deviceInformation: '設備資訊',
            ipAddress: 'IP 位址',
            type: '類型',
            vendor: '品牌',
            status: '狀態',
            metrics: '指標',
            cpu: 'CPU',
            memory: '記憶體',
            upstreamDevices: '上游設備',
            downstreamDevices: '下游設備',

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

            // Alerts page
            activeAlerts: '活躍告警',
            noActiveAlerts: '無告警',
            resolvedToday: '今日已解決',
            active: '活躍',
            all: '全部',
            acknowledgeAll: '全部確認',
            acknowledge: '確認',
            recentActivity: '最近活動',
            triggered: '已觸發',
            acknowledged: '已確認',
            acknowledgeReason: '確認原因',
            enterReason: '請輸入確認原因...',
            reasonRequired: '請輸入原因',
            highCpu: 'CPU 過高',
            highMemory: '記憶體過高',
            deviceOffline: '設備離線',
            linkHighUtilization: '連結使用率過高',
            info: '資訊',

            // Groups page
            newGroup: '+ 新增',
            editGroup: '編輯群組',
            groupName: '名稱',
            description: '描述',
            parentGroup: '父群組',
            noneTopLevel: '無 (頂層)',
            color: '顏色',
            selectAGroup: '選擇群組',
            unassigned: '未分配',
            noDevicesInGroup: '此群組無設備',
            moveSelectedTo: '移動選取項目至...',
            move: '移動',
            removeFromGroup: '從群組移除',

            // Settings page
            systemOverview: '系統概覽',
            totalDevices: '設備總數',
            totalLinks: '連結總數',
            snmpConfiguration: 'SNMP 設定',
            defaultCommunity: '預設社群字串',
            pollInterval: '輪詢間隔 (秒)',
            snmpTimeout: 'SNMP 逾時 (秒)',
            snmpRetries: 'SNMP 重試次數',
            saveSnmpSettings: '儲存 SNMP 設定',
            alertProfiles: '告警設定檔',
            newProfile: '+ 新增設定檔',
            logExport: '日誌匯出',
            enableLogExport: '啟用日誌匯出',
            exportType: '匯出類型',
            testConnection: '測試連線',
            notifications: '通知',
            browserNotifications: '瀏覽器通知',
            soundAlerts: '聲音警報',

            // Appearance settings
            appearance: '外觀',
            language: '語言',
            theme: '主題',

            // SNMP subnet restriction
            allowedSubnets: '允許的網段',
            allowedSubnetsLabel: '目標 IP 必須在以下網段內',
            enforceSubnetRestriction: '啟用網段限制',
            cidrHelpText: '每行一個 CIDR 格式網段，留空表示不限制',
            subnetRestrictionHelp: '啟用後，SNMP 測試和設備探索只能對允許網段內的 IP 進行',

            // SNMP Testing Tools
            snmpTestingTools: 'SNMP 測試工具',
            snmpConnectionTest: 'SNMP 連線測試',
            targetIp: '目標 IP',
            communityString: '社群字串',
            selectOid: '選擇 OID',
            customOid: '自訂 OID',
            testResult: '測試結果',
            manualDiscovery: '手動探索設備',
            startIp: '起始 IP',
            recursiveDiscovery: '遞迴探索 (發現 LLDP 鄰居)',
            recursiveDiscoveryHelp: '啟用後會自動探索發現設備的所有鄰居',
            startDiscovery: '開始探索',
            discoveryResult: '探索結果',
            discoveryIp: 'IP 位址',
            discoveryCommunity: '社群字串',
            oid: 'OID',
            oidOptional: 'OID (選填)',
            sysDescr: 'sysDescr - 系統描述',
            sysName: 'sysName - 主機名稱',
            sysUpTime: 'sysUpTime - 運行時間',
            lldpNeighbors: 'lldpRemTable - LLDP 鄰居',
            customOidOption: '自訂 OID...',

            // Dynamic messages
            enterTargetIp: '請輸入目標 IP',
            enterStartIp: '請輸入起始 IP',
            testing: '測試中...',
            discovering: '探索中...',
            discoveryComplete: '探索完成',
            discoveredDevices: '發現 {count} 個設備，新增 {added} 個',
            discoveryFailed: '探索失敗',
            testSuccess: '測試成功',
            testFailed: '測試失敗',
            settingsSaved: 'SNMP 設定已儲存',
            ipNotInSubnets: '❌ IP {ip} 不在允許的網段內\n\n允許的網段: {subnets}',
            notConfigured: '(未設定)',
            newDevice: '新增',
            alreadyExists: '已存在',

            // Details panel (extend)
            model: '型號',
            firmware: '韌體',
            lastSeen: '最後見到',
            hostname: '主機名稱',
            actions: '操作',

            // Common
            save: '儲存',
            cancel: '取消',
            delete: '刪除',
            edit: '編輯',
            add: '新增',
            close: '關閉',
            loading: '載入中...',
            error: '錯誤',
            success: '成功',
            confirm: '確認',
            viewFullDetails: '查看完整詳情',
            viewInTopology: '在拓撲圖中查看',
            addDevice: '+ 新增設備',
            searchHostnameOrIp: '搜尋主機名或 IP...',
            allStatus: '所有狀態',
            allVendors: '所有廠商',
            perPage: '/ 頁',
            showAll: '顯示全部',
            recovered: '已恢復',

            // Alert detail modal
            device: '設備',
            message: '訊息',
            timeline: '時間軸',
            triggeredAt: '觸發時間',
            affectedDownstreamDevices: '受影響的下游設備',
            devicesAffected: '個設備受影響',
            causedBy: '根本原因',
            offlineUpstreamFailure: '此設備因上游失敗而離線',
            viewRootCauseAlert: '查看根本原因告警 →',
            acknowledgeHistory: '確認歷史',

            // Device Modal
            autoDetect: '自動偵測',
            deviceType: '設備類型',
            snmpCommunity: 'SNMP 社群字串',
            alertProfile: '告警設定檔',
            autoDiscoverNeighbors: '自動探索鄰居設備',
            default: '預設',
            accessPoint: '無線基地台',
            editDevice: '編輯設備',

            // Alerts page
            acknowledge: '確認',
            acknowledgeAll: '全部確認',
            acknowledgeAlert: '確認告警',
            addNote: '新增記錄',
            acked: '已確認',
            ackHistory: '確認歷史',
            noAckHistory: '無確認記錄',
            enterReason: '請輸入原因：',
            reasonRequired: '請輸入原因',
            noDetails: '無詳細資訊',
            noAlerts: '🎉 沒有告警！一切運作正常。',
            resolvedToday: '今日已解決',
            activeAlerts: '活動告警',
            all: '全部',
            recentActivity: '最近活動',
            triggered: '已觸發',
            noRecentActivity: '無最近活動',

            // Suppress notifications
            suppressNotifications: '暫停推播',
            customDuration: '自訂時長',
            untilResolved: '直到解決',
            noSuppress: '不暫停',
            minutes: '分鐘',
            hours: '小時',
            days: '天',

            // History management
            noHistory: '無歷史記錄',
            noReason: '無原因',
            edit: '編輯',
            delete: '刪除',
            deletedBy: '刪除者',
            until: '至',
            notificationsSuppressed: '推播已暫停',
            resumeNotifications: '恢復推播',
            confirmUnsuppress: '確定要恢復此告警的推播嗎？',
            editReasonPrompt: '請輸入新原因：',
            deleteReasonPrompt: '請輸入刪除原因：',
            confirmRestoreNotifications: '刪除後是否恢復推播？',
            addNote: '新增記錄',
            enterNotePrompt: '請輸入新的確認記錄（將追加到歷史）：',
            errorLoadingHistory: '載入歷史時發生錯誤'
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
            deviceInformation: '设备信息',
            ipAddress: 'IP 地址',
            type: '类型',
            vendor: '品牌',
            status: '状态',
            metrics: '指标',
            cpu: 'CPU',
            memory: '内存',
            upstreamDevices: '上游设备',
            downstreamDevices: '下游设备',

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

            // Alerts page
            activeAlerts: '活跃告警',
            noActiveAlerts: '无告警',
            resolvedToday: '今日已解决',
            active: '活跃',
            all: '全部',
            acknowledgeAll: '全部确认',
            acknowledge: '确认',
            recentActivity: '最近活动',
            triggered: '已触发',
            acknowledged: '已确认',
            acknowledgeReason: '确认原因',
            enterReason: '请输入确认原因...',
            reasonRequired: '请输入原因',
            highCpu: 'CPU 过高',
            highMemory: '内存过高',
            deviceOffline: '设备离线',
            linkHighUtilization: '链接使用率过高',
            info: '信息',

            // Groups page
            newGroup: '+ 新建',
            editGroup: '编辑群组',
            groupName: '名称',
            description: '描述',
            parentGroup: '父群组',
            noneTopLevel: '无 (顶层)',
            color: '颜色',
            selectAGroup: '选择群组',
            unassigned: '未分配',
            noDevicesInGroup: '此群组无设备',
            moveSelectedTo: '移动选中项目至...',
            move: '移动',
            removeFromGroup: '从群组移除',

            // Settings page
            systemOverview: '系统概览',
            totalDevices: '设备总数',
            totalLinks: '链接总数',
            snmpConfiguration: 'SNMP 配置',
            defaultCommunity: '默认社区字符串',
            pollInterval: '轮询间隔 (秒)',
            snmpTimeout: 'SNMP 超时 (秒)',
            snmpRetries: 'SNMP 重试次数',
            saveSnmpSettings: '保存 SNMP 设置',
            alertProfiles: '告警配置文件',
            newProfile: '+ 新建配置文件',
            logExport: '日志导出',
            enableLogExport: '启用日志导出',
            exportType: '导出类型',
            testConnection: '测试连接',
            notifications: '通知',
            browserNotifications: '浏览器通知',
            soundAlerts: '声音警报',

            // Appearance settings
            appearance: '外观',
            language: '语言',
            theme: '主题',

            // SNMP subnet restriction
            allowedSubnets: '允许的网段',
            allowedSubnetsLabel: '目标 IP 必须在以下网段内',
            enforceSubnetRestriction: '启用网段限制',
            cidrHelpText: '每行一个 CIDR 格式网段，留空表示不限制',
            subnetRestrictionHelp: '启用后，SNMP 测试和设备探索只能对允许网段内的 IP 进行',

            // SNMP Testing Tools
            snmpTestingTools: 'SNMP 测试工具',
            snmpConnectionTest: 'SNMP 连接测试',
            targetIp: '目标 IP',
            communityString: '社区字符串',
            selectOid: '选择 OID',
            customOid: '自定义 OID',
            testResult: '测试结果',
            manualDiscovery: '手动探索设备',
            startIp: '起始 IP',
            recursiveDiscovery: '递归探索 (发现 LLDP 邻居)',
            discoveryResult: '探索结果',
            discoveryIp: 'IP 地址',
            discoveryCommunity: '社区字符串',
            oid: 'OID',
            oidOptional: 'OID (选填)',
            recursiveDiscoveryHelp: '启用后会自动探索发现设备的所有邻居',
            startDiscovery: '开始探索',
            sysDescr: 'sysDescr - 系统描述',
            sysName: 'sysName - 主机名称',
            sysUpTime: 'sysUpTime - 运行时间',
            lldpNeighbors: 'lldpRemTable - LLDP 邻居',
            customOidOption: '自定义 OID...',

            // Dynamic messages
            enterTargetIp: '请输入目标 IP',
            enterStartIp: '请输入起始 IP',
            testing: '测试中...',
            discovering: '探索中...',
            discoveryComplete: '探索完成',
            discoveredDevices: '发现 {count} 个设备，新增 {added} 个',
            discoveryFailed: '探索失败',
            testSuccess: '测试成功',
            testFailed: '测试失败',
            settingsSaved: 'SNMP 设定已保存',
            ipNotInSubnets: '❌ IP {ip} 不在允许的网段内\n\n允许的网段: {subnets}',
            notConfigured: '(未设定)',
            newDevice: '新增',
            alreadyExists: '已存在',

            // Details panel (extend)
            model: '型号',
            firmware: '固件',
            lastSeen: '最后见到',
            hostname: '主机名',
            actions: '操作',

            // Common
            save: '保存',
            cancel: '取消',
            delete: '删除',
            edit: '编辑',
            add: '添加',
            close: '关闭',
            loading: '加载中...',
            error: '错误',
            success: '成功',
            confirm: '确认',
            viewFullDetails: '查看完整详情',
            viewInTopology: '在拓扑图中查看',
            addDevice: '+ 添加设备',
            searchHostnameOrIp: '搜索主机名或 IP...',
            allStatus: '所有状态',
            allVendors: '所有厂商',
            perPage: '/ 页',
            showAll: '显示全部',
            recovered: '已恢复',

            // Alert detail modal
            device: '设备',
            message: '消息',
            timeline: '时间线',
            triggeredAt: '触发时间',
            affectedDownstreamDevices: '受影响的下游设备',
            devicesAffected: '个设备受影响',
            causedBy: '根本原因',
            offlineUpstreamFailure: '此设备因上游故障而离线',
            viewRootCauseAlert: '查看根本原因告警 →',
            acknowledgeHistory: '确认历史',

            // Device Modal
            autoDetect: '自动检测',
            deviceType: '设备类型',
            snmpCommunity: 'SNMP 社区字符串',
            alertProfile: '告警配置',
            autoDiscoverNeighbors: '自动发现邻居设备',
            default: '默认',
            accessPoint: '无线接入点',
            editDevice: '编辑设备',

            // Alerts page
            acknowledge: '确认',
            acknowledgeAll: '全部确认',
            acknowledgeAlert: '确认告警',
            addNote: '添加记录',
            acked: '已确认',
            ackHistory: '确认历史',
            noAckHistory: '无确认记录',
            enterReason: '请输入原因：',
            reasonRequired: '请输入原因',
            noDetails: '无详细信息',
            noAlerts: '🎉 没有告警！一切运行正常。',
            resolvedToday: '今日已解决',
            activeAlerts: '活动告警',
            all: '全部',
            recentActivity: '最近活动',
            triggered: '已触发',
            noRecentActivity: '无最近活动',

            // Suppress notifications
            suppressNotifications: '暂停推送',
            customDuration: '自定义时长',
            untilResolved: '直到解决',
            noSuppress: '不暂停',
            minutes: '分钟',
            hours: '小时',
            days: '天',

            // History management
            noHistory: '无历史记录',
            noReason: '无原因',
            edit: '编辑',
            delete: '删除',
            deletedBy: '删除者',
            until: '至',
            notificationsSuppressed: '推送已暂停',
            resumeNotifications: '恢复推送',
            confirmUnsuppress: '确定要恢复此告警的推送吗？',
            editReasonPrompt: '请输入新原因：',
            deleteReasonPrompt: '请输入删除原因：',
            confirmRestoreNotifications: '删除后是否恢复推送？',
            addNote: '添加记录',
            enterNotePrompt: '请输入新的确认记录（将追加到历史）：',
            errorLoadingHistory: '加载历史时发生错误'
        }
    },

    init() {
        // Load saved language or default to English
        const saved = localStorage.getItem('language');
        if (saved && this.translations[saved]) {
            this.currentLang = saved;
        } else {
            // Default to English when no saved preference
            this.currentLang = 'en';
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
