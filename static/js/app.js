/**
 * Main Application JavaScript
 * Handles API calls, UI interactions, and data management
 */

class App {
    constructor() {
        this.apiBase = '/api/v1';
        this.topology = null;
        this.currentView = 'overview';
        this.refreshInterval = null;

        this.init();
    }

    async init() {
        // Initialize topology graph
        this.topology = new TopologyGraph('#topology-svg');
        this.topology.onNodeClick = (node) => this.showNodeDetails(node);
        this.topology.onLinkClick = (link) => this.showLinkDetails(link);

        // Set up event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadTopology();
        await this.loadAlerts();
        await this.loadGroups();

        // Start auto-refresh
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // View selector buttons
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setView(e.target.dataset.view);
            });
        });

        // Refresh button
        document.getElementById('refresh-btn')?.addEventListener('click', () => {
            this.loadTopology();
        });

        // Fit button
        document.getElementById('fit-btn')?.addEventListener('click', () => {
            this.topology.fitView();
        });

        // Group select
        document.getElementById('group-select')?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadTopology('group', e.target.value);
            }
        });

        // Panel close button
        document.getElementById('panel-close')?.addEventListener('click', () => {
            this.hideDetailPanel();
        });
    }

    async setView(view) {
        // Update active button
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        // Show/hide group select
        const groupSelect = document.getElementById('group-select');
        if (groupSelect) {
            groupSelect.style.display = view === 'group' ? 'block' : 'none';
        }

        this.currentView = view;
        await this.loadTopology(view);
    }

    async loadTopology(view = this.currentView, groupId = null) {
        this.showLoading(true);

        try {
            let url = `${this.apiBase}/topology?view=${view}`;
            if (groupId) url += `&group_id=${groupId}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to load topology');

            const data = await response.json();
            this.topology.setData(data);
            this.updateLastUpdate(data.last_updated);

            // Auto-fit on initial load
            setTimeout(() => this.topology.fitView(), 500);

        } catch (error) {
            console.error('Error loading topology:', error);
            this.showError('Failed to load topology data');
        } finally {
            this.showLoading(false);
        }
    }

    async loadAlerts() {
        try {
            const response = await fetch(`${this.apiBase}/alerts/active`);
            if (!response.ok) throw new Error('Failed to load alerts');

            const data = await response.json();
            this.renderAlerts(data.alerts);

        } catch (error) {
            console.error('Error loading alerts:', error);
        }
    }

    async loadGroups() {
        try {
            const response = await fetch(`${this.apiBase}/groups`);
            if (!response.ok) throw new Error('Failed to load groups');

            const groups = await response.json();
            this.renderGroupOptions(groups);

        } catch (error) {
            console.error('Error loading groups:', error);
        }
    }

    renderAlerts(alerts) {
        const countEl = document.getElementById('alerts-count');
        const listEl = document.getElementById('alerts-list');

        if (countEl) countEl.textContent = alerts.length;

        if (listEl) {
            listEl.innerHTML = alerts.map(alert => `
                <div class="alert-item ${alert.severity}">
                    <span class="alert-message">${alert.message || alert.alert_type}</span>
                    <span class="alert-time">${this.formatTime(alert.triggered_at)}</span>
                </div>
            `).join('') || '<p style="padding: 0.5rem; color: var(--text-secondary);">No active alerts</p>';
        }
    }

    renderGroupOptions(groups) {
        const select = document.getElementById('group-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select Group...</option>' +
            groups.map(g => `<option value="${g.id}">${g.name} (${g.device_count})</option>`).join('');
    }

    showNodeDetails(node) {
        const panel = document.getElementById('detail-panel');
        const title = document.getElementById('panel-title');
        const content = document.getElementById('panel-content');

        if (!panel || !title || !content) return;

        title.textContent = node.hostname;
        content.innerHTML = `
            <div class="detail-section">
                <h4>Device Info</h4>
                <div class="detail-row">
                    <span class="detail-label">IP Address</span>
                    <span class="detail-value">${node.ip_address}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type</span>
                    <span class="detail-value">${node.device_type || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Vendor</span>
                    <span class="detail-value">${node.vendor || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status</span>
                    <span class="detail-value">${node.status}</span>
                </div>
            </div>
            <div class="detail-section">
                <h4>Metrics</h4>
                <div class="detail-row">
                    <span class="detail-label">CPU</span>
                    <span class="detail-value">${node.cpu_percent ? node.cpu_percent.toFixed(1) + '%' : 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Memory</span>
                    <span class="detail-value">${node.memory_percent ? node.memory_percent.toFixed(1) + '%' : 'N/A'}</span>
                </div>
            </div>
            ${node.alert_count > 0 ? `
            <div class="detail-section">
                <h4>Alerts (${node.alert_count})</h4>
                <p style="color: var(--danger);">This device has active alerts</p>
            </div>
            ` : ''}
        `;

        panel.style.display = 'flex';
    }

    showLinkDetails(link) {
        const panel = document.getElementById('detail-panel');
        const title = document.getElementById('panel-title');
        const content = document.getElementById('panel-content');

        if (!panel || !title || !content) return;

        const sourceNode = this.topology.nodes.find(n => n.id === link.source.id || n.id === link.source);
        const targetNode = this.topology.nodes.find(n => n.id === link.target.id || n.id === link.target);

        title.textContent = 'Link Details';
        content.innerHTML = `
            <div class="detail-section">
                <h4>Connection</h4>
                <div class="detail-row">
                    <span class="detail-label">From</span>
                    <span class="detail-value">${sourceNode?.hostname || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">To</span>
                    <span class="detail-value">${targetNode?.hostname || 'Unknown'}</span>
                </div>
            </div>
            <div class="detail-section">
                <h4>Bandwidth</h4>
                <div class="detail-row">
                    <span class="detail-label">Total</span>
                    <span class="detail-value">${this.formatBandwidth(link.total_bandwidth_mbps)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">In Utilization</span>
                    <span class="detail-value">${link.utilization_in_percent?.toFixed(1) || 0}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Out Utilization</span>
                    <span class="detail-value">${link.utilization_out_percent?.toFixed(1) || 0}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status</span>
                    <span class="detail-value" style="color: var(--${this.getStatusColor(link.status)})">${link.status}</span>
                </div>
            </div>
            ${link.port_details?.length ? `
            <div class="detail-section">
                <h4>Port Details</h4>
                <div class="port-list">
                    ${link.port_details.map(p => `
                        <div class="port-item">
                            <span class="port-name">${p.local_port} ↔ ${p.remote_port}</span>
                            <span class="port-util">${this.formatBandwidth(p.bandwidth_mbps)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        `;

        panel.style.display = 'flex';
    }

    hideDetailPanel() {
        const panel = document.getElementById('detail-panel');
        if (panel) panel.style.display = 'none';
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = show ? 'flex' : 'none';
    }

    showError(message) {
        // Simple error display - can be enhanced
        console.error(message);
        alert(message);
    }

    updateLastUpdate(timestamp) {
        const el = document.getElementById('last-update');
        if (el && timestamp) {
            const date = new Date(timestamp);
            el.textContent = `Last update: ${date.toLocaleTimeString()}`;
        }
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }

    formatBandwidth(mbps) {
        if (!mbps) return 'N/A';
        if (mbps >= 1000) return `${(mbps / 1000).toFixed(0)}G`;
        return `${mbps}M`;
    }

    getStatusColor(status) {
        const colors = {
            normal: 'success',
            elevated: 'elevated',
            warning: 'warning',
            critical: 'danger'
        };
        return colors[status] || 'text-secondary';
    }

    startAutoRefresh() {
        // Refresh every 60 seconds
        this.refreshInterval = setInterval(() => {
            this.loadTopology();
            this.loadAlerts();
        }, 60000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
