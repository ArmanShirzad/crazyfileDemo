// Main application logic for Crazyflie Swarm Demo
class SwarmApp {
    constructor() {
        this.drones = new Map();
        this.selectedDrone = null;
        this.isConnected = false;
        this.updateInterval = null;
        
        this.init();
    }

    async init() {
        // Initialize visualization
        visualization = new SwarmVisualization('three-container');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check connection
        await this.checkConnection();
        
        // Start periodic updates
        this.startUpdates();
    }

    setupEventListeners() {
        // Connection status
        this.updateConnectionStatus();

        // Swarm control
        document.getElementById('create-swarm').addEventListener('click', () => this.createSwarm());
        document.getElementById('emergency-stop').addEventListener('click', () => this.emergencyStop());
        document.getElementById('reset-simulation').addEventListener('click', () => this.resetSimulation());

        // Drone control
        document.getElementById('drone-select').addEventListener('change', (e) => {
            this.selectedDrone = e.target.value;
        });
        document.getElementById('takeoff-btn').addEventListener('click', () => this.takeoff());
        document.getElementById('land-btn').addEventListener('click', () => this.land());
        document.getElementById('goto-btn').addEventListener('click', () => this.goto());

        // Formations
        document.getElementById('set-formation').addEventListener('click', () => this.setFormation());

        // Experiments
        document.getElementById('run-experiment').addEventListener('click', () => this.runExperiment());

        // Camera controls
        document.getElementById('reset-camera').addEventListener('click', () => visualization.resetCamera());
        document.getElementById('toggle-grid').addEventListener('click', () => visualization.toggleGrid());

        // Export controls
        document.getElementById('export-csv').addEventListener('click', () => experimentManager.exportData('csv'));
        document.getElementById('export-json').addEventListener('click', () => experimentManager.exportData('json'));
    }

    async checkConnection() {
        try {
            this.isConnected = await api.healthCheck();
            this.updateConnectionStatus();
        } catch (error) {
            this.isConnected = false;
            this.updateConnectionStatus();
        }
    }

    updateConnectionStatus() {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        
        if (this.isConnected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Disconnected';
        }
    }

    async createSwarm() {
        if (!this.isConnected) {
            alert('Not connected to backend');
            return;
        }

        const count = parseInt(document.getElementById('swarm-count').value);
        if (count < 1 || count > 10) {
            alert('Please enter a count between 1 and 10');
            return;
        }

        try {
            const result = await api.createSwarm(count);
            this.updateDroneSelect(result.drones);
            this.showSuccess(`Created swarm with ${count} drones`);
        } catch (error) {
            this.showError(`Failed to create swarm: ${error.message}`);
        }
    }

    async emergencyStop() {
        if (!this.isConnected) {
            alert('Not connected to backend');
            return;
        }

        try {
            await api.emergencyStop();
            this.showSuccess('Emergency stop executed');
        } catch (error) {
            this.showError(`Emergency stop failed: ${error.message}`);
        }
    }

    async resetSimulation() {
        if (!this.isConnected) {
            alert('Not connected to backend');
            return;
        }

        if (confirm('Are you sure you want to reset the simulation? This will clear all drones and data.')) {
            try {
                await api.resetSimulation();
                visualization.clearAllDrones();
                this.drones.clear();
                this.updateDroneSelect([]);
                experimentManager.clearHistory();
                this.showSuccess('Simulation reset');
            } catch (error) {
                this.showError(`Reset failed: ${error.message}`);
            }
        }
    }

    async takeoff() {
        if (!this.selectedDrone) {
            alert('Please select a drone first');
            return;
        }

        try {
            await api.takeoff(this.selectedDrone, 0.6, 2.0);
            this.showSuccess(`Drone ${this.selectedDrone} taking off`);
        } catch (error) {
            this.showError(`Takeoff failed: ${error.message}`);
        }
    }

    async land() {
        if (!this.selectedDrone) {
            alert('Please select a drone first');
            return;
        }

        try {
            await api.land(this.selectedDrone);
            this.showSuccess(`Drone ${this.selectedDrone} landing`);
        } catch (error) {
            this.showError(`Landing failed: ${error.message}`);
        }
    }

    async goto() {
        if (!this.selectedDrone) {
            alert('Please select a drone first');
            return;
        }

        const x = parseFloat(document.getElementById('target-x').value);
        const y = parseFloat(document.getElementById('target-y').value);
        const z = parseFloat(document.getElementById('target-z').value);

        if (isNaN(x) || isNaN(y) || isNaN(z)) {
            alert('Please enter valid coordinates');
            return;
        }

        try {
            await api.goto(this.selectedDrone, x, y, z, 0.5);
            this.showSuccess(`Drone ${this.selectedDrone} moving to (${x}, ${y}, ${z})`);
        } catch (error) {
            this.showError(`Goto failed: ${error.message}`);
        }
    }

    async setFormation() {
        if (!this.isConnected) {
            alert('Not connected to backend');
            return;
        }

        const formation = document.getElementById('formation-select').value;
        const radius = 1.0; // Default radius
        const height = 0.6; // Default height

        // Check if any drones are flying
        const states = await api.getDrones();
        const flyingDrones = Object.values(states).filter(d => d.status === 'flying');
        
        if (flyingDrones.length === 0) {
            this.showError('No flying drones found. Please takeoff some drones first!');
            return;
        }

        try {
            await api.setFormation(formation, { radius, height });
            this.showSuccess(`Formation set for ${flyingDrones.length} flying drone(s)`);
        } catch (error) {
            this.showError(`Formation failed: ${error.message}`);
        }
    }

    async runExperiment() {
        if (!this.isConnected) {
            alert('Not connected to backend');
            return;
        }

        const scenario = document.getElementById('experiment-select').value;
        const duration = parseInt(document.getElementById('experiment-duration').value);
        const count = parseInt(document.getElementById('swarm-count').value);

        if (duration < 5 || duration > 60) {
            alert('Please enter a duration between 5 and 60 seconds');
            return;
        }

        try {
            this.showInfo(`Running ${scenario} experiment...`);
            const result = await experimentManager.runExperiment(scenario, count, duration);
            this.showSuccess(`Experiment completed: ${result.runId}`);
        } catch (error) {
            this.showError(`Experiment failed: ${error.message}`);
        }
    }

    updateDroneSelect(droneIds) {
        const select = document.getElementById('drone-select');
        select.innerHTML = '<option value="">Select a drone</option>';
        
        droneIds.forEach(id => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = id;
            select.appendChild(option);
        });
    }

    startUpdates() {
        // Update drone states every 100ms (10Hz)
        this.updateInterval = setInterval(() => {
            this.updateDroneStates();
        }, 100);
    }

    async updateDroneStates() {
        if (!this.isConnected) return;

        try {
            const states = await api.getDrones();
            
            // Update visualization
            Object.entries(states).forEach(([id, state]) => {
                visualization.updateDrone(id, state);
                this.drones.set(id, state);
            });

            // Update state panel
            this.updateStatePanel(states);
            
            // Update swarm statistics
            this.updateSwarmStats(states);

        } catch (error) {
            // Silently handle connection errors during updates
            if (error.message.includes('Failed to fetch')) {
                this.isConnected = false;
                this.updateConnectionStatus();
            }
        }
    }

    updateStatePanel(states) {
        const container = document.getElementById('drone-states');
        container.innerHTML = '';

        Object.entries(states).forEach(([id, state]) => {
            const stateDiv = document.createElement('div');
            stateDiv.className = `drone-state ${state.status}`;
            
            stateDiv.innerHTML = `
                <h4>${id}</h4>
                <div class="state-info">
                    <div><strong>Position:</strong> (${state.x.toFixed(2)}, ${state.y.toFixed(2)}, ${state.z.toFixed(2)})</div>
                    <div><strong>Velocity:</strong> (${state.vx.toFixed(2)}, ${state.vy.toFixed(2)}, ${state.vz.toFixed(2)})</div>
                    <div><strong>Battery:</strong> ${state.battery.toFixed(1)}%</div>
                    <div><strong>Status:</strong> ${state.status}</div>
                </div>
            `;
            
            container.appendChild(stateDiv);
        });
    }

    updateSwarmStats(states) {
        const container = document.getElementById('swarm-stats');
        
        const numDrones = Object.keys(states).length;
        const flyingDrones = Object.values(states).filter(s => s.status === 'flying').length;
        const avgBattery = Object.values(states).reduce((sum, s) => sum + s.battery, 0) / numDrones || 0;
        
        container.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Total Drones:</span>
                <span class="stat-value">${numDrones}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Flying:</span>
                <span class="stat-value">${flyingDrones}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Avg Battery:</span>
                <span class="stat-value">${avgBattery.toFixed(1)}%</span>
            </div>
        `;
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type) {
        // Simple notification system - could be enhanced with a proper toast library
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;

        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#27ae60';
                break;
            case 'error':
                notification.style.backgroundColor = '#e74c3c';
                break;
            case 'info':
                notification.style.backgroundColor = '#3498db';
                break;
        }

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.swarmApp = new SwarmApp();
});

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
