#!/bin/bash

# Crazyflie Firmware Setup Script
# Installs ARM GCC toolchain and dependencies

set -e

echo "Setting up Crazyflie firmware build environment..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is designed for Linux systems"
    echo "For other platforms, please use Docker or install ARM GCC manually"
    exit 1
fi

# Check if ARM GCC is already installed
if command -v arm-none-eabi-gcc &> /dev/null; then
    echo "ARM GCC toolchain already installed"
    arm-none-eabi-gcc --version
else
    echo "Installing ARM GCC toolchain..."
    
    # Create tools directory
    mkdir -p ~/tools
    cd ~/tools
    
    # Download ARM GCC toolchain
    ARM_GCC_VERSION="10.3-2021.10"
    ARM_GCC_URL="https://developer.arm.com/-/media/Files/downloads/gnu-rm/${ARM_GCC_VERSION}/gcc-arm-none-eabi-${ARM_GCC_VERSION}-x86_64-linux.tar.bz2"
    
    echo "Downloading ARM GCC ${ARM_GCC_VERSION}..."
    wget -O arm-gcc.tar.bz2 "$ARM_GCC_URL"
    
    echo "Extracting ARM GCC..."
    tar -xjf arm-gcc.tar.bz2
    
    # Add to PATH
    echo "Adding ARM GCC to PATH..."
    echo 'export PATH="$HOME/tools/gcc-arm-none-eabi-${ARM_GCC_VERSION}/bin:$PATH"' >> ~/.bashrc
    
    # Source bashrc for current session
    export PATH="$HOME/tools/gcc-arm-none-eabi-${ARM_GCC_VERSION}/bin:$PATH"
    
    echo "ARM GCC installation complete"
fi

# Install additional dependencies
echo "Installing additional dependencies..."

# Update package list
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    make \
    git \
    python3 \
    python3-pip \
    python3-venv \
    libusb-1.0-0-dev \
    libusb-1.0-0 \
    pkg-config \
    libffi-dev \
    libssl-dev

# Install Python packages
echo "Installing Python packages..."
pip3 install --user \
    pyusb \
    libusb1 \
    cflib \
    crazyflie-lib-python

# Install Crazyflie client tools
echo "Installing Crazyflie client tools..."
pip3 install --user cfclient

# Create virtual environment for firmware development
echo "Creating Python virtual environment..."
python3 -m venv ~/crazyflie-env
source ~/crazyflie-env/bin/activate

# Install development tools
pip install \
    pytest \
    pytest-cov \
    black \
    flake8

echo "Setup complete!"
echo ""
echo "To use the ARM GCC toolchain in new terminal sessions:"
echo "  source ~/.bashrc"
echo ""
echo "To activate the Python environment:"
echo "  source ~/crazyflie-env/bin/activate"
echo ""
echo "To test the installation:"
echo "  arm-none-eabi-gcc --version"
echo "  python3 -c 'import cflib; print(\"CFLib installed successfully\")'"
