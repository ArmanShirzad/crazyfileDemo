// Experiment management and data visualization
class ExperimentManager {
    constructor() {
        this.currentRunId = null;
        this.experimentHistory = [];
        this.charts = {};
        this.chartData = {
            position: { labels: [], datasets: [] },
            battery: { labels: [], datasets: [] }
        };
        
        this.initCharts();
    }

    initCharts() {
        // Position chart
        const positionCtx = document.getElementById('position-chart').getContext('2d');
        this.charts.position = new Chart(positionCtx, {
            type: 'line',
            data: this.chartData.position,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Position (m)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });

        // Battery chart
        const batteryCtx = document.getElementById('battery-chart').getContext('2d');
        this.charts.battery = new Chart(batteryCtx, {
            type: 'line',
            data: this.chartData.battery,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Battery (%)'
                        },
                        min: 0,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }

    async runExperiment(scenario, numDrones, duration, parameters = {}) {
        try {
            const result = await api.runExperiment(scenario, numDrones, duration, parameters);
            
            if (result.success) {
                this.currentRunId = result.runId;
                this.addExperimentResult(result);
                
                // Start monitoring the experiment
                this.monitorExperiment(result.runId, duration);
                
                return result;
            } else {
                throw new Error(result.error || 'Experiment failed');
            }
        } catch (error) {
            console.error('Experiment failed:', error);
            this.showError(`Experiment failed: ${error.message}`);
            throw error;
        }
    }

    async monitorExperiment(runId, duration) {
        const startTime = Date.now();
        const endTime = startTime + (duration * 1000);
        
        const monitorInterval = setInterval(async () => {
            try {
                // Update charts with latest data
                await this.updateCharts(runId);
                
                // Check if experiment is complete
                if (Date.now() >= endTime) {
                    clearInterval(monitorInterval);
                    await this.finalizeExperiment(runId);
                }
            } catch (error) {
                console.error('Error monitoring experiment:', error);
            }
        }, 1000); // Update every second
    }

    async updateCharts(runId) {
        try {
            const logs = await api.getLogs(runId);
            if (!logs.samples || logs.samples.length === 0) return;

            // Group samples by drone
            const droneData = {};
            logs.samples.forEach(sample => {
                if (!droneData[sample.droneId]) {
                    droneData[sample.droneId] = [];
                }
                droneData[sample.droneId].push(sample);
            });

            // Update position chart
            this.updatePositionChart(droneData);
            
            // Update battery chart
            this.updateBatteryChart(droneData);
            
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    updatePositionChart(droneData) {
        const datasets = [];
        const colors = ['#0ea5e9', '#06b6d4', '#0891b2', '#0d9488', '#059669'];
        
        Object.keys(droneData).forEach((droneId, index) => {
            const samples = droneData[droneId];
            const color = colors[index % colors.length];
            
            // X position
            datasets.push({
                label: `${droneId} X`,
                data: samples.map(s => ({ x: s.t, y: s.x })),
                borderColor: color,
                backgroundColor: color + '20',
                fill: false,
                tension: 0.1
            });
            
            // Y position
            datasets.push({
                label: `${droneId} Y`,
                data: samples.map(s => ({ x: s.t, y: s.y })),
                borderColor: color,
                backgroundColor: color + '20',
                fill: false,
                tension: 0.1,
                borderDash: [5, 5]
            });
            
            // Z position
            datasets.push({
                label: `${droneId} Z`,
                data: samples.map(s => ({ x: s.t, y: s.z })),
                borderColor: color,
                backgroundColor: color + '20',
                fill: false,
                tension: 0.1,
                borderDash: [10, 5]
            });
        });

        this.charts.position.data.datasets = datasets;
        this.charts.position.update('none');
    }

    updateBatteryChart(droneData) {
        const datasets = [];
        const colors = ['#0ea5e9', '#06b6d4', '#0891b2', '#0d9488', '#059669'];
        
        Object.keys(droneData).forEach((droneId, index) => {
            const samples = droneData[droneId];
            const color = colors[index % colors.length];
            
            datasets.push({
                label: droneId,
                data: samples.map(s => ({ x: s.t, y: s.battery })),
                borderColor: color,
                backgroundColor: color + '20',
                fill: false,
                tension: 0.1
            });
        });

        this.charts.battery.data.datasets = datasets;
        this.charts.battery.update('none');
    }

    addExperimentResult(result) {
        this.experimentHistory.unshift(result);
        this.updateResultsDisplay();
    }

    updateResultsDisplay() {
        const container = document.getElementById('experiment-results');
        container.innerHTML = '';

        this.experimentHistory.forEach((result, index) => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'experiment-result';
            
            const statusClass = result.success ? 'text-success' : 'text-error';
            const statusText = result.success ? 'Success' : 'Failed';
            
            resultDiv.innerHTML = `
                <h4>${result.scenario} - ${statusText}</h4>
                <div class="result-info">
                    <p><strong>Run ID:</strong> ${result.runId}</p>
                    <p><strong>Duration:</strong> ${result.duration}s</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    ${result.error ? `<p class="text-error"><strong>Error:</strong> ${result.error}</p>` : ''}
                </div>
            `;
            
            container.appendChild(resultDiv);
        });
    }

    async finalizeExperiment(runId) {
        try {
            // Get final logs
            const logs = await api.getLogs(runId);
            
            // Calculate metrics
            const metrics = this.calculateMetrics(logs.samples);
            
            // Update result with metrics
            const result = this.experimentHistory.find(r => r.runId === runId);
            if (result) {
                result.metrics = metrics;
                result.completed = true;
                this.updateResultsDisplay();
            }
            
        } catch (error) {
            console.error('Error finalizing experiment:', error);
        }
    }

    calculateMetrics(samples) {
        if (!samples || samples.length === 0) {
            return { pathLength: 0, flightTime: 0, minSeparation: Infinity };
        }

        // Group by drone
        const droneData = {};
        samples.forEach(sample => {
            if (!droneData[sample.droneId]) {
                droneData[sample.droneId] = [];
            }
            droneData[sample.droneId].push(sample);
        });

        let totalPathLength = 0;
        let minSeparation = Infinity;
        let flightTime = 0;

        // Calculate path length for each drone
        Object.values(droneData).forEach(droneSamples => {
            let pathLength = 0;
            for (let i = 1; i < droneSamples.length; i++) {
                const prev = droneSamples[i - 1];
                const curr = droneSamples[i];
                const dx = curr.x - prev.x;
                const dy = curr.y - prev.y;
                const dz = curr.z - prev.z;
                pathLength += Math.sqrt(dx * dx + dy * dy + dz * dz);
            }
            totalPathLength += pathLength;
        });

        // Calculate minimum separation between drones
        const droneIds = Object.keys(droneData);
        for (let i = 0; i < droneIds.length; i++) {
            for (let j = i + 1; j < droneIds.length; j++) {
                const drone1 = droneData[droneIds[i]];
                const drone2 = droneData[droneIds[j]];
                
                // Find minimum separation over time
                const minLength = Math.min(drone1.length, drone2.length);
                for (let k = 0; k < minLength; k++) {
                    const dx = drone1[k].x - drone2[k].x;
                    const dy = drone1[k].y - drone2[k].y;
                    const dz = drone1[k].z - drone2[k].z;
                    const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
                    minSeparation = Math.min(minSeparation, distance);
                }
            }
        }

        // Calculate flight time
        if (samples.length > 0) {
            flightTime = samples[samples.length - 1].t - samples[0].t;
        }

        return {
            pathLength: totalPathLength,
            flightTime: flightTime,
            minSeparation: minSeparation === Infinity ? 0 : minSeparation,
            numDrones: droneIds.length
        };
    }

    async exportData(format) {
        if (!this.currentRunId) {
            this.showError('No experiment data to export');
            return;
        }

        try {
            const data = await api.getLogs(this.currentRunId, format);
            
            if (format === 'csv') {
                this.downloadCSV(data, `experiment_${this.currentRunId}.csv`);
            } else {
                this.downloadJSON(data, `experiment_${this.currentRunId}.json`);
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.showError(`Export failed: ${error.message}`);
        }
    }

    downloadCSV(data, filename) {
        if (!data.samples) return;
        
        const headers = ['time', 'droneId', 'x', 'y', 'z', 'vx', 'vy', 'vz', 'battery', 'status'];
        const csvContent = [
            headers.join(','),
            ...data.samples.map(sample => 
                headers.map(header => sample[header] || '').join(',')
            )
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        this.downloadBlob(blob, filename);
    }

    downloadJSON(data, filename) {
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    }

    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showError(message) {
        // Simple error display - could be enhanced with a proper notification system
        console.error(message);
        alert(message);
    }

    clearHistory() {
        this.experimentHistory = [];
        this.updateResultsDisplay();
        this.charts.position.data.datasets = [];
        this.charts.battery.data.datasets = [];
        this.charts.position.update();
        this.charts.battery.update();
    }
}

// Global experiment manager instance
const experimentManager = new ExperimentManager();
