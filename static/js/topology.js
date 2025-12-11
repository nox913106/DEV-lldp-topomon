/**
 * D3.js Topology Visualization
 * Handles network topology graph rendering and interaction
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
        
        this.nodeRadius = 20;
        this.onNodeClick = null;
        this.onLinkClick = null;
        
        this.init();
    }
    
    init() {
        // Get dimensions
        const rect = this.svg.node().getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = rect.height || 600;
        
        // Set up zoom
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
        
        this.svg.call(this.zoom);
        
        // Create main group
        this.g = this.svg.append('g');
        
        // Create groups for links and nodes
        this.linksGroup = this.g.append('g').attr('class', 'links');
        this.nodesGroup = this.g.append('g').attr('class', 'nodes');
        this.labelsGroup = this.g.append('g').attr('class', 'labels');
        
        // Arrow marker for directed links
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#8b949e');
        
        // Initialize simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(50));
        
        // Handle window resize
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
    
    render() {
        // Clear existing
        this.linksGroup.selectAll('*').remove();
        this.nodesGroup.selectAll('*').remove();
        this.labelsGroup.selectAll('*').remove();
        
        if (this.nodes.length === 0) return;
        
        // Render links
        const linkElements = this.linksGroup.selectAll('line')
            .data(this.links)
            .join('line')
            .attr('class', d => `link status-${d.status}`)
            .attr('stroke-width', d => this.getLinkWidth(d.total_bandwidth_mbps))
            .on('click', (event, d) => {
                if (this.onLinkClick) this.onLinkClick(d);
            });
        
        // Render link labels
        const linkLabels = this.labelsGroup.selectAll('.link-label')
            .data(this.links)
            .join('text')
            .attr('class', 'link-label')
            .text(d => this.formatBandwidth(d.total_bandwidth_mbps));
        
        // Render nodes
        const nodeElements = this.nodesGroup.selectAll('.node')
            .data(this.nodes)
            .join('g')
            .attr('class', d => `node status-${d.status === 'managed' ? 'online' : d.status}`)
            .call(this.drag())
            .on('click', (event, d) => {
                if (this.onNodeClick) this.onNodeClick(d);
            });
        
        // Node circles
        nodeElements.append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => this.getNodeStroke(d));
        
        // Node icons/type indicator
        nodeElements.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '12px')
            .text(d => this.getNodeIcon(d));
        
        // Node labels
        nodeElements.append('text')
            .attr('dy', 35)
            .attr('text-anchor', 'middle')
            .attr('class', 'node-label')
            .text(d => d.hostname);
        
        // Alert badge
        nodeElements.filter(d => d.alert_count > 0)
            .append('circle')
            .attr('cx', 15)
            .attr('cy', -15)
            .attr('r', 8)
            .attr('fill', '#f85149');
        
        nodeElements.filter(d => d.alert_count > 0)
            .append('text')
            .attr('x', 15)
            .attr('y', -15)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '10px')
            .attr('fill', 'white')
            .text(d => d.alert_count);
        
        // Update simulation
        this.simulation.nodes(this.nodes).on('tick', () => {
            linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            linkLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2 - 10);
            
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
    
    getNodeRadius(node) {
        const type = (node.device_type || '').toLowerCase();
        if (type.includes('core')) return 30;
        if (type.includes('dist')) return 25;
        return 20;
    }
    
    getNodeColor(node) {
        if (node.status === 'offline') return '#f85149';
        if (node.status === 'managed') return '#3fb950';
        return '#8b949e';
    }
    
    getNodeStroke(node) {
        if (node.status === 'offline') return '#da3633';
        if (node.status === 'managed') return '#2ea043';
        return '#6e7681';
    }
    
    getNodeIcon(node) {
        const type = (node.device_type || '').toLowerCase();
        if (type.includes('core') || type.includes('router')) return '🔷';
        if (type.includes('dist')) return '🔶';
        if (type.includes('firewall')) return '🛡️';
        return '📦';
    }
    
    getLinkWidth(bandwidthMbps) {
        if (bandwidthMbps >= 100000) return 8;  // 100G
        if (bandwidthMbps >= 40000) return 6;   // 40G
        if (bandwidthMbps >= 10000) return 4;   // 10G
        if (bandwidthMbps >= 1000) return 3;    // 1G
        return 2;
    }
    
    formatBandwidth(mbps) {
        if (mbps >= 1000) return `${mbps / 1000}G`;
        return `${mbps}M`;
    }
    
    fitView() {
        if (this.nodes.length === 0) return;
        
        const bounds = this.g.node().getBBox();
        const padding = 50;
        
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
}

// Export for use
window.TopologyGraph = TopologyGraph;
