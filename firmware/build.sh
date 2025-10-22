#!/bin/bash

# Crazyflie Firmware Build Script
# Builds the official crazyflie-firmware with custom configurations

set -e

echo "Building Crazyflie firmware..."

# Check if ARM GCC is available
if ! command -v arm-none-eabi-gcc &> /dev/null; then
    echo "Error: ARM GCC toolchain not found"
    echo "Please run ./setup.sh first or use Docker"
    exit 1
fi

# Create build directory
BUILD_DIR="build"
FIRMWARE_DIR="crazyflie-firmware"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clone or update firmware repository
if [ ! -d "$FIRMWARE_DIR" ]; then
    echo "Cloning crazyflie-firmware repository..."
    git clone https://github.com/bitcraze/crazyflie-firmware.git "$FIRMWARE_DIR"
else
    echo "Updating crazyflie-firmware repository..."
    cd "$FIRMWARE_DIR"
    git pull
    cd ..
fi

cd "$FIRMWARE_DIR"

# Checkout stable version
echo "Checking out stable version..."
git checkout master
git pull

# Apply custom configurations
echo "Applying custom configurations..."

# Copy custom PID configurations
if [ -f "../../configs/pid_aggressive.h" ]; then
    echo "Applying aggressive PID configuration..."
    cp "../../configs/pid_aggressive.h" src/modules/src/controller_pid_aggressive.h
fi

if [ -f "../../configs/pid_smooth.h" ]; then
    echo "Applying smooth PID configuration..."
    cp "../../configs/pid_smooth.h" src/modules/src/controller_pid_smooth.h
fi

# Apply custom build configuration
echo "Applying build configuration..."

# Create custom config file
cat > config.mk << EOF
# Custom configuration for swarm demo
CFLAGS += -DDEBUG_PRINT_ON_UART1
CFLAGS += -DENABLE_DEBUG_PRINT
CFLAGS += -DUSE_AGGRESSIVE_PID

# Optimization flags
CFLAGS += -O2
CFLAGS += -ffast-math
CFLAGS += -funroll-loops

# Enable additional features
CFLAGS += -DENABLE_SWARM_MODE
CFLAGS += -DENABLE_COLLISION_AVOIDANCE
CFLAGS += -DENABLE_FORMATION_FLIGHT

# Communication settings
CFLAGS += -DRADIO_CHANNEL=80
CFLAGS += -DRADIO_DATARATE=2M
CFLAGS += -DRADIO_POWER=0

# Safety settings
CFLAGS += -DMAX_VELOCITY=1.0
CFLAGS += -DMAX_ACCELERATION=2.0
CFLAGS += -DBATTERY_LOW_THRESHOLD=3.7
EOF

# Build firmware
echo "Building firmware..."
make clean
make

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build successful!"
    
    # Copy binaries to build directory
    echo "Copying binaries..."
    cp build/cf2.bin ../cf2.bin
    cp build/cf2.elf ../cf2.elf
    cp build/cf2.hex ../cf2.hex
    
    # Generate build info
    echo "Generating build information..."
    cat > ../build_info.txt << EOF
Build Date: $(date)
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git branch --show-current)
ARM GCC Version: $(arm-none-eabi-gcc --version | head -n1)
Build Configuration: Custom swarm demo
EOF
    
    echo ""
    echo "Build completed successfully!"
    echo "Binaries available in: $(pwd)/../"
    echo "- cf2.bin: Binary firmware file"
    echo "- cf2.elf: ELF executable file"
    echo "- cf2.hex: Intel HEX file"
    echo "- build_info.txt: Build information"
    
else
    echo "Build failed!"
    exit 1
fi

cd ../..

echo "Firmware build complete!"
