// API client for Crazyflie Swarm Demo
class SwarmAPI {
    constructor() {
        this.baseURL = this.getBaseURL();
        this.token = 'demo-token';
        this.isConnected = false;
    }

    getBaseURL() {
        // Determine API base URL based on environment
        if (location.hostname === 'localhost' || 
            location.hostname === '127.0.0.1' || 
            location.hostname === '0.0.0.0' ||
            location.hostname === '') {
            return 'http://localhost:8000';
        } else if (location.hostname.includes('github.io')) {
            // GitHub Pages deployment - use Railway backend
            return 'https://devoted-education-production-22b3.up.railway.app';
        } else {
            // Production URL - actual Railway URL
            return 'https://devoted-education-production-22b3.up.railway.app';
        }
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed: ${error.message}`);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            this.isConnected = response.ok;
            return this.isConnected;
        } catch (error) {
            this.isConnected = false;
            return false;
        }
    }

    // Swarm management
    async createSwarm(count) {
        return await this.makeRequest('/drones/create', {
            method: 'POST',
            body: JSON.stringify({ count })
        });
    }

    async getDrones() {
        return await this.makeRequest('/drones', {
            method: 'GET',
            headers: {} // No auth required for read-only
        });
    }

    async resetSimulation() {
        return await this.makeRequest('/drones', {
            method: 'DELETE'
        });
    }

    // Drone control
    async takeoff(droneId, height = 0.6, duration = 2.0) {
        return await this.makeRequest(`/drones/${droneId}/takeoff`, {
            method: 'POST',
            body: JSON.stringify({ height, duration })
        });
    }

    async goto(droneId, x, y, z, speed = 0.5) {
        return await this.makeRequest(`/drones/${droneId}/goto`, {
            method: 'POST',
            body: JSON.stringify({ x, y, z, speed })
        });
    }

    async land(droneId) {
        return await this.makeRequest(`/drones/${droneId}/land`, {
            method: 'POST'
        });
    }

    async getDroneState(droneId) {
        return await this.makeRequest(`/drones/${droneId}/state`, {
            method: 'GET',
            headers: {} // No auth required for read-only
        });
    }

    // Swarm operations
    async setFormation(formation, parameters = {}) {
        return await this.makeRequest('/swarm/formation', {
            method: 'POST',
            body: JSON.stringify({ formation, parameters })
        });
    }

    // Experiments
    async runExperiment(scenario, numDrones, duration, parameters = {}) {
        return await this.makeRequest('/experiments/run', {
            method: 'POST',
            body: JSON.stringify({ scenario, numDrones, duration, parameters })
        });
    }

    // Data export
    async getLogs(runId, format = 'json') {
        return await this.makeRequest(`/logs?runId=${runId}&format=${format}`, {
            method: 'GET',
            headers: {} // No auth required for read-only
        });
    }

    // Emergency operations
    async emergencyStop() {
        return await this.makeRequest('/emergency/stop', {
            method: 'POST'
        });
    }

    // Algorithm validation
    async validateAlgorithm(algorithm, testCases) {
        return await this.makeRequest('/validate/algorithm', {
            method: 'POST',
            body: JSON.stringify({ algorithm, testCases })
        });
    }
}

// Global API instance
const api = new SwarmAPI();
