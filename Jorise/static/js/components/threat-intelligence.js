/* =============================================================================
   THREAT INTELLIGENCE COMPONENT
   Real-time threat visualization and updates
   ============================================================================= */

class ThreatIntelligence {
    constructor() {
        this.threats = [];
        this.updateInterval = null;
        this.init();
    }

    init() {
        this.loadThreats();
        this.startRealTimeUpdates();
    }

    loadThreats() {
        // Simulate threat data
        this.threats = [
            { name: 'Trojan.GenKryptor', severity: 'high', count: 156, blocked: 156 },
            { name: 'Ransom.Lockbit', severity: 'critical', count: 23, blocked: 23 },
            { name: 'Adware.BrowseFox', severity: 'medium', count: 89, blocked: 87 }
        ];
        
        this.renderThreats();
    }

    renderThreats() {
        const container = document.getElementById('threat-list');
        if (!container) return;

        container.innerHTML = this.threats.map(threat => `
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg mb-2">
                <div>
                    <span class="font-medium text-gray-900">${threat.name}</span>
                    <span class="ml-2 px-2 py-1 text-xs rounded-full ${this.getSeverityColor(threat.severity)}">
                        ${threat.severity.toUpperCase()}
                    </span>
                </div>
                <div class="text-right">
                    <div class="text-sm font-medium">${threat.blocked}/${threat.count}</div>
                    <div class="text-xs text-gray-500">Blocked</div>
                </div>
            </div>
        `).join('');
    }

    getSeverityColor(severity) {
        const colors = {
            'low': 'bg-blue-100 text-blue-800',
            'medium': 'bg-yellow-100 text-yellow-800',
            'high': 'bg-orange-100 text-orange-800',
            'critical': 'bg-red-100 text-red-800'
        };
        return colors[severity] || colors['medium'];
    }

    startRealTimeUpdates() {
        this.updateInterval = setInterval(() => {
            this.updateThreatCounts();
        }, 15000);
    }

    updateThreatCounts() {
        this.threats.forEach(threat => {
            threat.count += Math.floor(Math.random() * 3);
            threat.blocked = Math.min(threat.blocked + Math.floor(Math.random() * 3), threat.count);
        });
        
        this.renderThreats();
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('threat-list')) {
        window.threatIntelligence = new ThreatIntelligence();
    }
});