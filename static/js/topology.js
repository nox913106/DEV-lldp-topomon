/**
 * D3.js Topology Visualization
 * Network topology graph with Cisco-style device icons
 */

class TopologyGraph {
    constructor(containerId) {
        this.container = d3.select(containerId);
        this.svg = this.container;
        this.width = 0;
        this.height = 0;
        this.nodes = [];
        this.links = [];
        this.simulation = null;
        this.g = null;
        this.zoom = null;

        this.onNodeClick = null;
        this.onLinkClick = null;

        // Device icons (Cisco-style SVG paths)
        this.deviceIcons = {
            router: `<svg viewBox="0 0 64 64" width="48" height="48">
                <rect x="8" y="20" width="48" height="24" rx="4" fill="#1a73e8" stroke="#0d47a1" stroke-width="2"/>
                <line x1="16" y1="28" x2="16" y2="36" stroke="white" stroke-width="2"/>
                <line x1="24" y1="28" x2="24" y2="36" stroke="white" stroke-width="2"/>
                <line x1="32" y1="28" x2="32" y2="36" stroke="white" stroke-width="2"/>
                <line x1="40" y1="28" x2="40" y2="36" stroke="white" stroke-width="2"/>
                <line x1="48" y1="28" x2="48" y2="36" stroke="white" stroke-width="2"/>
                <circle cx="32" cy="10" r="6" fill="#1a73e8" stroke="#0d47a1" stroke-width="2"/>
                <line x1="32" y1="16" x2="32" y2="20" stroke="#0d47a1" stroke-width="2"/>
            </svg>`,
            core: `<svg viewBox="0 0 64 64" width="52" height="52">
                <rect x="6" y="18" width="52" height="28" rx="4" fill="#6200ea" stroke="#4a148c" stroke-width="2"/>
                <rect x="12" y="24" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="22" y="24" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="32" y="24" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="42" y="24" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="12" y="34" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="22" y="34" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="32" y="34" width="8" height="6" rx="1" fill="#b388ff"/>
                <rect x="42" y="34" width="8" height="6" rx="1" fill="#b388ff"/>
                <polygon points="32,2 38,12 26,12" fill="#6200ea" stroke="#4a148c" stroke-width="1"/>
            </svg>`,
            distribution: `<svg viewBox="0 0 64 64" width="48" height="48">
                <rect x="8" y="18" width="48" height="28" rx="4" fill="#00897b" stroke="#004d40" stroke-width="2"/>
                <rect x="14" y="24" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="22" y="24" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="30" y="24" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="38" y="24" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="14" y="34" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="22" y="34" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="30" y="34" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="38" y="34" width="6" height="6" rx="1" fill="#80cbc4"/>
                <rect x="46" y="24" width="6" height="16" rx="1" fill="#4db6ac"/>
            </svg>`,
            access: `<svg viewBox="0 0 64 64" width="44" height="44">
                <rect x="10" y="20" width="44" height="24" rx="3" fill="#43a047" stroke="#2e7d32" stroke-width="2"/>
                <rect x="16" y="26" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="22" y="26" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="28" y="26" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="34" y="26" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="40" y="26" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="16" y="33" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="22" y="33" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="28" y="33" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="34" y="33" width="4" height="5" rx="1" fill="#a5d6a7"/>
                <rect x="40" y="33" width="4" height="5" rx="1" fill="#a5d6a7"/>
            </svg>`,
            firewall: `<svg viewBox="0 0 64 64" width="48" height="48">
                <rect x="8" y="16" width="48" height="32" rx="4" fill="#e53935" stroke="#b71c1c" stroke-width="2"/>
                <rect x="16" y="24" width="32" height="16" rx="2" fill="#ffcdd2"/>
                <path d="M28 28 L32 24 L36 28 L32 40 Z" fill="#e53935"/>
                <line x1="20" y1="10" x2="20" y2="16" stroke="#e53935" stroke-width="2"/>
                <line x1="32" y1="8" x2="32" y2="16" stroke="#e53935" stroke-width="2"/>
                <line x1="44" y1="10" x2="44" y2="16" stroke="#e53935" stroke-width="2"/>
            </svg>`,
            ap: `<svg viewBox="0 0 64 64" width="44" height="44">
                <ellipse cx="32" cy="36" rx="20" ry="8" fill="#fb8c00" stroke="#e65100" stroke-width="2"/>
                <rect x="28" y="28" width="8" height="8" fill="#fb8c00" stroke="#e65100" stroke-width="2"/>
                <path d="M20 20 Q32 8 44 20" fill="none" stroke="#fb8c00" stroke-width="2"/>
                <path d="M24 24 Q32 16 40 24" fill="none" stroke="#ffb74d" stroke-width="2"/>
                <circle cx="32" cy="18" r="3" fill="#ffb74d"/>
            </svg>`,
            unknown: `<svg viewBox="0 0 64 64" width="40" height="40">
                <rect x="12" y="16" width="40" height="32" rx="4" fill="#78909c" stroke="#455a64" stroke-width="2"/>
                <text x="32" y="38" text-anchor="middle" fill="white" font-size="16">?</text>
            </svg>`
        };

        this.init();
    }

    init() {
        const rect = this.svg.node().getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = rect.height || 600;

        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        this.g = this.svg.append('g');

        this.linksGroup = this.g.append('g').attr('class', 'links');
        this.nodesGroup = this.g.append('g').attr('class', 'nodes');

        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(180))
            .force('charge', d3.forceManyBody().strength(-600))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(80));

        window.addEventListener('resize', () => this.handleResize());
    }

    handleResize() {
        const rect = this.svg.node().getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = rect.height || 600;

        this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
        this.simulation.alpha(0.3).restart();
    }

    setData(data) {
        this.nodes = data.nodes || [];
        this.links = data.links || [];
        this.render();
    }

    getDeviceType(node) {
        const type = (node.device_type || '').toLowerCase();
        if (type.includes('core')) return 'core';
        if (type.includes('dist')) return 'distribution';
        if (type.includes('router')) return 'router';
        if (type.includes('access') || type === 'switch') return 'access';
        if (type.includes('firewall')) return 'firewall';
        if (type.includes('ap') || type.includes('wireless')) return 'ap';
        return 'unknown';
    }

    formatVendor(vendor) {
        const vendors = {
            'cisco_ios': 'Cisco IOS',
            'cisco_nxos': 'Cisco NX-OS',
            'hp_aruba': 'HP/Aruba',
            'fortinet': 'Fortinet',
            'paloalto': 'Palo Alto',
            'ruckus': 'Ruckus'
        };
        return vendors[vendor] || vendor || 'Unknown';
    }

    render() {
        this.linksGroup.selectAll('*').remove();
        this.nodesGroup.selectAll('*').remove();

        if (this.nodes.length === 0) return;

        // Render links
        const linkElements = this.linksGroup.selectAll('g.link-group')
            .data(this.links)
            .join('g')
            .attr('class', 'link-group');

        linkElements.append('line')
            .attr('class', d => `link status-${d.status}`)
            .attr('stroke-width', d => this.getLinkWidth(d.total_bandwidth_mbps))
            .on('click', (event, d) => {
                if (this.onLinkClick) this.onLinkClick(d);
            });

        // Link bandwidth labels
        linkElements.append('text')
            .attr('class', 'link-label')
            .attr('text-anchor', 'middle')
            .attr('dy', -8)
            .text(d => this.formatBandwidth(d.total_bandwidth_mbps));

        // Link utilization labels
        linkElements.append('text')
            .attr('class', 'link-util')
            .attr('text-anchor', 'middle')
            .attr('dy', 12)
            .text(d => {
                const maxUtil = Math.max(d.utilization_in_percent || 0, d.utilization_out_percent || 0);
                return `${maxUtil.toFixed(0)}%`;
            });

        // Render nodes
        const nodeElements = this.nodesGroup.selectAll('g.node')
            .data(this.nodes)
            .join('g')
            .attr('class', d => `node device-${this.getDeviceType(d)} status-${d.status === 'managed' ? 'online' : d.status}`)
            .call(this.drag())
            .on('click', (event, d) => {
                if (this.onNodeClick) this.onNodeClick(d);
            });

        // Device icon using foreignObject
        nodeElements.append('foreignObject')
            .attr('width', 52)
            .attr('height', 52)
            .attr('x', -26)
            .attr('y', -26)
            .html(d => this.deviceIcons[this.getDeviceType(d)] || this.deviceIcons.unknown);

        // Offline overlay
        nodeElements.filter(d => d.status === 'offline')
            .append('rect')
            .attr('x', -26)
            .attr('y', -26)
            .attr('width', 52)
            .attr('height', 52)
            .attr('rx', 4)
            .attr('fill', 'rgba(248, 81, 73, 0.5)')
            .attr('stroke', '#f85149')
            .attr('stroke-width', 2);

        // Vendor label (above icon)
        nodeElements.append('text')
            .attr('dy', -35)
            .attr('text-anchor', 'middle')
            .attr('class', 'node-vendor')
            .attr('fill', '#8b949e')
            .attr('font-size', '10px')
            .text(d => this.formatVendor(d.vendor));

        // Hostname label
        nodeElements.append('text')
            .attr('dy', 40)
            .attr('text-anchor', 'middle')
            .attr('class', 'node-hostname')
            .attr('fill', '#e6edf3')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text(d => d.hostname);

        // IP address label
        nodeElements.append('text')
            .attr('dy', 54)
            .attr('text-anchor', 'middle')
            .attr('class', 'node-ip')
            .attr('fill', '#8b949e')
            .attr('font-size', '10px')
            .text(d => d.ip_address);

        // Alert badge
        nodeElements.filter(d => d.alert_count > 0)
            .append('circle')
            .attr('cx', 22)
            .attr('cy', -22)
            .attr('r', 10)
            .attr('fill', '#f85149')
            .attr('stroke', '#da3633')
            .attr('stroke-width', 2);

        nodeElements.filter(d => d.alert_count > 0)
            .append('text')
            .attr('x', 22)
            .attr('y', -22)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '11px')
            .attr('font-weight', 'bold')
            .attr('fill', 'white')
            .text(d => d.alert_count);

        // Simulation tick handler
        this.simulation.nodes(this.nodes).on('tick', () => {
            linkElements.select('line')
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkElements.selectAll('text')
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);

            nodeElements.attr('transform', d => `translate(${d.x}, ${d.y})`);
        });

        this.simulation.force('link').links(this.links);
        this.simulation.alpha(1).restart();
    }

    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    getLinkWidth(bandwidthMbps) {
        if (bandwidthMbps >= 100000) return 10;  // 100G
        if (bandwidthMbps >= 40000) return 8;   // 40G
        if (bandwidthMbps >= 10000) return 6;   // 10G
        if (bandwidthMbps >= 1000) return 4;    // 1G
        return 2;
    }

    formatBandwidth(mbps) {
        if (mbps >= 1000) return `${mbps / 1000}G`;
        return `${mbps}M`;
    }

    fitView() {
        if (this.nodes.length === 0) return;

        const bounds = this.g.node().getBBox();
        const padding = 80;

        const scale = Math.min(
            this.width / (bounds.width + padding * 2),
            this.height / (bounds.height + padding * 2)
        );

        const centerX = bounds.x + bounds.width / 2;
        const centerY = bounds.y + bounds.height / 2;

        this.svg.transition().duration(750).call(
            this.zoom.transform,
            d3.zoomIdentity
                .translate(this.width / 2, this.height / 2)
                .scale(Math.min(scale, 1))
                .translate(-centerX, -centerY)
        );
    }

    resetZoom() {
        this.svg.transition().duration(500).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }

    updateTheme(theme) {
        // Update text colors based on theme
        const textColor = theme === 'light' ? '#1f2328' : '#e6edf3';
        const secondaryColor = theme === 'light' ? '#656d76' : '#8b949e';
        const linkLabelColor = theme === 'light' ? '#0969da' : '#58a6ff';

        this.nodesGroup.selectAll('.node-hostname')
            .attr('fill', textColor);

        this.nodesGroup.selectAll('.node-vendor')
            .attr('fill', secondaryColor);

        this.nodesGroup.selectAll('.node-ip')
            .attr('fill', secondaryColor);

        this.linksGroup.selectAll('.link-label')
            .attr('fill', linkLabelColor);

        this.linksGroup.selectAll('.link-util')
            .attr('fill', secondaryColor);
    }
}

window.TopologyGraph = TopologyGraph;
