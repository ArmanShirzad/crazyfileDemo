// Three.js visualization for Crazyflie Swarm Demo
class SwarmVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.drones = new Map();
        this.trails = new Map();
        this.grid = null;
        this.axes = null;
        this.animationId = null;
        
        this.init();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f9ff);

        // Create camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(5, 5, 5);
        this.camera.lookAt(0, 0, 0);

        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        // Add lighting
        this.setupLighting();

        // Add grid and axes
        this.addGrid();
        this.addAxes();

        // Setup controls
        this.setupControls();

        // Start animation loop
        this.animate();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
    }

    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);

        // Directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        this.scene.add(directionalLight);
    }

    addGrid() {
        const gridSize = 4;
        const gridDivisions = 20;
        const gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x888888, 0xcccccc);
        gridHelper.position.y = -0.01; // Slightly below ground to avoid z-fighting
        this.scene.add(gridHelper);
        this.grid = gridHelper;
    }

    addAxes() {
        const axesHelper = new THREE.AxesHelper(2);
        this.scene.add(axesHelper);
        this.axes = axesHelper;
    }

    setupControls() {
        // Simple orbit controls using mouse
        let isMouseDown = false;
        let mouseX = 0, mouseY = 0;
        let targetX = 0, targetY = 0;

        this.renderer.domElement.addEventListener('mousedown', (event) => {
            isMouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        this.renderer.domElement.addEventListener('mouseup', () => {
            isMouseDown = false;
        });

        this.renderer.domElement.addEventListener('mousemove', (event) => {
            if (!isMouseDown) return;

            const deltaX = event.clientX - mouseX;
            const deltaY = event.clientY - mouseY;

            targetX += deltaX * 0.01;
            targetY += deltaY * 0.01;

            // Constrain vertical rotation
            targetY = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, targetY));

            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        this.renderer.domElement.addEventListener('wheel', (event) => {
            const delta = event.deltaY * 0.01;
            this.camera.position.multiplyScalar(1 + delta);
        });

        // Store control state
        this.controls = { targetX, targetY };
    }

    updateControls() {
        if (!this.controls) return;

        // Smooth camera movement
        const radius = this.camera.position.length();
        const x = radius * Math.cos(this.controls.targetY) * Math.sin(this.controls.targetX);
        const y = radius * Math.sin(this.controls.targetY);
        const z = radius * Math.cos(this.controls.targetY) * Math.cos(this.controls.targetX);

        this.camera.position.set(x, y, z);
        this.camera.lookAt(0, 0, 0);
    }

    createDrone(id, x = 0, y = 0, z = 0) {
        // Create drone geometry
        const geometry = new THREE.BoxGeometry(0.1, 0.1, 0.05);
        const material = new THREE.MeshLambertMaterial({ color: 0x666666 });
        const drone = new THREE.Mesh(geometry, material);

        // Add drone ID label
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 64;
        const context = canvas.getContext('2d');
        context.fillStyle = 'rgba(0, 0, 0, 0.8)';
        context.fillRect(0, 0, 128, 64);
        context.fillStyle = 'white';
        context.font = '16px Arial';
        context.textAlign = 'center';
        context.fillText(id, 64, 40);

        const texture = new THREE.CanvasTexture(canvas);
        const labelMaterial = new THREE.SpriteMaterial({ map: texture });
        const label = new THREE.Sprite(labelMaterial);
        label.scale.set(0.5, 0.25, 1);
        label.position.set(0, 0.2, 0);
        drone.add(label);

        // Position drone
        drone.position.set(x, y, z);
        drone.castShadow = true;
        drone.receiveShadow = true;

        // Add to scene
        this.scene.add(drone);
        this.drones.set(id, drone);

        // Initialize trail
        this.trails.set(id, []);

        return drone;
    }

    updateDrone(id, state) {
        let drone = this.drones.get(id);
        if (!drone) {
            drone = this.createDrone(id, state.x, state.y, state.z);
        }

        // Update position
        drone.position.set(state.x, state.y, state.z);

        // Update color based on status
        const material = drone.material;
        switch (state.status) {
            case 'flying':
                material.color.setHex(0x27ae60); // Green
                break;
            case 'takingOff':
                material.color.setHex(0xf39c12); // Orange
                break;
            case 'landing':
                material.color.setHex(0xe67e22); // Dark orange
                break;
            case 'error':
                material.color.setHex(0xe74c3c); // Red
                break;
            default:
                material.color.setHex(0x666666); // Gray
        }

        // Update trail
        this.updateTrail(id, state.x, state.y, state.z);
    }

    updateTrail(id, x, y, z) {
        const trail = this.trails.get(id);
        if (!trail) return;

        // Add new point
        trail.push(new THREE.Vector3(x, y, z));

        // Keep only last 50 points (about 2.5 seconds at 20Hz)
        if (trail.length > 50) {
            trail.shift();
        }

        // Update trail visualization
        this.updateTrailVisualization(id, trail);
    }

    updateTrailVisualization(id, trail) {
        // Remove existing trail
        const existingTrail = this.scene.getObjectByName(`trail_${id}`);
        if (existingTrail) {
            this.scene.remove(existingTrail);
        }

        if (trail.length < 2) return;

        // Create new trail geometry
        const geometry = new THREE.BufferGeometry().setFromPoints(trail);
        const material = new THREE.LineBasicMaterial({ 
            color: 0x0ea5e9,
            opacity: 0.6,
            transparent: true
        });
        const trailLine = new THREE.Line(geometry, material);
        trailLine.name = `trail_${id}`;
        this.scene.add(trailLine);
    }

    removeDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            this.scene.remove(drone);
            this.drones.delete(id);
        }

        // Remove trail
        const trail = this.scene.getObjectByName(`trail_${id}`);
        if (trail) {
            this.scene.remove(trail);
        }
        this.trails.delete(id);
    }

    clearAllDrones() {
        this.drones.forEach((drone, id) => {
            this.removeDrone(id);
        });
    }

    toggleGrid() {
        if (this.grid) {
            this.grid.visible = !this.grid.visible;
        }
    }

    toggleAxes() {
        if (this.axes) {
            this.axes.visible = !this.axes.visible;
        }
    }

    resetCamera() {
        this.camera.position.set(5, 5, 5);
        this.camera.lookAt(0, 0, 0);
        this.controls.targetX = 0;
        this.controls.targetY = 0;
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        this.updateControls();
        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.renderer) {
            this.renderer.dispose();
        }
    }
}

// Global visualization instance
let visualization = null;
