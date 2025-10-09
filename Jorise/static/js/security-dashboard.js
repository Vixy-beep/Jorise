/* =============================================================================
   JORISE V2 ENTERPRISE - SECURITY DASHBOARD
   Frontend Developer: Main dashboard controller with real-time updates
   Dependencies: None (Vanilla JS)
   ============================================================================= */

class SecurityDashboard {
    constructor() {
        this.metrics = {
            threatsBlocked: 1247,
            activeIncidents: 5,
            endpointsProtected: 156,
            systemUptime: 99.97
        };
        
        this.init();
    }

    init() {
        this.initCounters();
        this.initProgressBars();
        this.initRealTimeUpdates();
        this.initInteractions();
    }

    // Animate counter numbers
    initCounters() {
        document.querySelectorAll('[data-counter]').forEach(element => {
            const target = parseInt(element.dataset.counter);
            this.animateCounter(element, target);
        });
    }

    animateCounter(element, target) {
        let current = 0;
        const increment = target / 100;
        const duration = 2000; // 2 seconds
        const stepTime = duration / 100;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target.toLocaleString();
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current).toLocaleString();
            }
        }, stepTime);
    }

    // Initialize progress bars with animation
    initProgressBars() {
        document.querySelectorAll('[data-progress]').forEach(bar => {
            const percentage = parseInt(bar.dataset.progress);
            setTimeout(() => {
                bar.style.width = `${percentage}%`;
            }, 500);
        });
    }

    // Simulate real-time updates
    initRealTimeUpdates() {
        setInterval(() => {
            this.updateThreatLevel();
            this.updateActiveIncidents();
        }, 30000); // Update every 30 seconds
    }

    updateThreatLevel() {
        const indicator = document.getElementById('threat-indicator');
        if (indicator) {
            // Simulate threat level changes
            const levels = ['bg-green-500', 'bg-yellow-500', 'bg-red-500'];
            const currentLevel = Math.floor(Math.random() * levels.length);
            
            indicator.className = `threat-indicator ${levels[currentLevel]}`;
        }
    }

    updateActiveIncidents() {
        const incidentCount = document.getElementById('incident-count');
        if (incidentCount) {
            // Simulate incident count changes
            const newCount = Math.floor(Math.random() * 10);
            this.animateCounter(incidentCount, newCount);
        }
    }

    // Handle interactive elements
    initInteractions() {
        // Security card hover effects
        document.querySelectorAll('.security-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.classList.add('animate-fade-scale');
            });
            
            card.addEventListener('mouseleave', () => {
                card.classList.remove('animate-fade-scale');
            });
        });

        // Module status toggles
        document.querySelectorAll('[data-module]').forEach(module => {
            module.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleModuleStatus(module);
            });
        });
    }

    toggleModuleStatus(moduleElement) {
        const statusBadge = moduleElement.querySelector('.status-badge');
        const alertCount = moduleElement.querySelector('[data-alerts]');
        
        if (statusBadge) {
            // Simulate status change
            const statuses = ['Online', 'Maintenance', 'Offline'];
            const colors = ['bg-green-100 text-green-800', 'bg-yellow-100 text-yellow-800', 'bg-red-100 text-red-800'];
            const currentIndex = Math.floor(Math.random() * statuses.length);
            
            statusBadge.textContent = statuses[currentIndex];
            statusBadge.className = `status-badge ${colors[currentIndex]}`;
        }
    }

    // Public method to update metrics
    updateMetrics(newMetrics) {
        Object.assign(this.metrics, newMetrics);
        this.initCounters();
    }

    // Export data for reports
    exportSecurityData() {
        return {
            timestamp: new Date().toISOString(),
            metrics: this.metrics,
            systemStatus: 'operational',
            threatLevel: 'low'
        };
    }
}

// Initialize dashboard when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    window.securityDashboard = new SecurityDashboard();
    
    // Make it globally accessible for frontend debugging
    console.log('🛡️ Security Dashboard initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityDashboard;
}