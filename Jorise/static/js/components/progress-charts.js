/* =============================================================================
   PROGRESS CHARTS COMPONENT
   Pure CSS progress bars replacing Chart.js
   ============================================================================= */

class ProgressCharts {
    constructor() {
        this.init();
    }

    init() {
        this.createCircularProgress();
        this.createBarCharts();
        this.animateCharts();
    }

    // Create circular progress (replaces donut charts)
    createCircularProgress() {
        document.querySelectorAll('[data-circular-progress]').forEach(element => {
            const percentage = parseInt(element.dataset.circularProgress);
            const color = element.dataset.color || '#3b82f6';
            
            element.innerHTML = `
                <div class="relative w-32 h-32">
                    <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" 
                                fill="none" 
                                stroke="#e5e7eb" 
                                stroke-width="8"/>
                        <circle cx="50" cy="50" r="45" 
                                fill="none" 
                                stroke="${color}" 
                                stroke-width="8" 
                                stroke-linecap="round"
                                stroke-dasharray="283" 
                                stroke-dashoffset="${283 - (283 * percentage) / 100}"
                                class="transition-all duration-1000 ease-out"/>
                    </svg>
                    <div class="absolute inset-0 flex items-center justify-center">
                        <span class="text-2xl font-bold text-gray-700">${percentage}%</span>
                    </div>
                </div>
            `;
        });
    }

    // Create horizontal bar charts
    createBarCharts() {
        document.querySelectorAll('[data-bar-chart]').forEach(container => {
            const data = JSON.parse(container.dataset.barChart);
            
            container.innerHTML = data.map(item => `
                <div class="mb-4">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-sm font-medium text-gray-700">${item.label}</span>
                        <span class="text-sm text-gray-500">${item.value}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${this.getBarColor(item.value)}" 
                             style="width: 0%" 
                             data-width="${item.value}%">
                        </div>
                    </div>
                </div>
            `).join('');
        });
    }

    getBarColor(value) {
        if (value >= 80) return 'bg-green-500';
        if (value >= 60) return 'bg-blue-500';
        if (value >= 40) return 'bg-yellow-500';
        return 'bg-red-500';
    }

    // Animate all charts
    animateCharts() {
        setTimeout(() => {
            // Animate bar charts
            document.querySelectorAll('.progress-fill[data-width]').forEach(bar => {
                bar.style.width = bar.dataset.width;
            });

            // Animate circular progress
            document.querySelectorAll('circle[stroke-dashoffset]').forEach(circle => {
                circle.style.transition = 'stroke-dashoffset 1s ease-out';
            });
        }, 500);
    }

    // Method to update chart data
    updateChart(containerId, newData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (container.hasAttribute('data-circular-progress')) {
            container.dataset.circularProgress = newData.percentage;
            this.createCircularProgress();
        } else if (container.hasAttribute('data-bar-chart')) {
            container.dataset.barChart = JSON.stringify(newData);
            this.createBarCharts();
            this.animateCharts();
        }
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    window.progressCharts = new ProgressCharts();
});