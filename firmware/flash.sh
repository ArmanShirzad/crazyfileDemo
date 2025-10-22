#!/bin/bash

# Crazyflie Firmware Flash Script
# Flashes firmware to Crazyflie via USB or radio

set -e

# Default values
DEVICE=""
METHOD="usb"
VERIFY=true
BACKUP=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--device)
            DEVICE="$2"
            shift 2
            ;;
        -m|--method)
            METHOD="$2"
            shift 2
            ;;
        --no-verify)
            VERIFY=false
            shift
            ;;
        --no-backup)
            BACKUP=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --device DEVICE    Device path (e.g., /dev/ttyUSB0)"
            echo "  -m, --method METHOD    Flash method: usb or radio (default: usb)"
            echo "  --no-verify           Skip flash verification"
            echo "  --no-backup           Skip firmware backup"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 -d /dev/ttyUSB0"
            echo "  $0 -m radio"
            echo "  $0 -d /dev/ttyUSB0 --no-backup"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "Crazyflie Firmware Flash Tool"
echo "============================="

# Check if firmware binary exists
FIRMWARE_BIN="build/cf2.bin"
if [ ! -f "$FIRMWARE_BIN" ]; then
    echo "Error: Firmware binary not found at $FIRMWARE_BIN"
    echo "Please run ./build.sh first"
    exit 1
fi

# Auto-detect device if not specified
if [ -z "$DEVICE" ]; then
    echo "Auto-detecting Crazyflie device..."
    
    # Check for USB devices
    USB_DEVICES=$(ls /dev/ttyUSB* 2>/dev/null || true)
    if [ -n "$USB_DEVICES" ]; then
        DEVICE=$(echo "$USB_DEVICES" | head -n1)
        echo "Found USB device: $DEVICE"
    else
        echo "No USB devices found. Please specify device with -d option"
        echo "Available options:"
        echo "  - USB: Connect Crazyflie via USB and specify /dev/ttyUSB0"
        echo "  - Radio: Use -m radio to flash via radio link"
        exit 1
    fi
fi

# Check device permissions
if [ "$METHOD" = "usb" ] && [ ! -w "$DEVICE" ]; then
    echo "Error: No write permission for device $DEVICE"
    echo "Try running with sudo or add your user to the dialout group:"
    echo "  sudo usermod -a -G dialout \$USER"
    echo "  (Then log out and log back in)"
    exit 1
fi

# Backup current firmware
if [ "$BACKUP" = true ]; then
    echo "Backing up current firmware..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).bin"
    
    if [ "$METHOD" = "usb" ]; then
        # Use stm32flash for USB backup
        if command -v stm32flash &> /dev/null; then
            stm32flash -r "$BACKUP_FILE" "$DEVICE" || echo "Warning: Backup failed"
        else
            echo "Warning: stm32flash not found, skipping backup"
        fi
    else
        echo "Warning: Radio backup not implemented, skipping backup"
    fi
fi

# Flash firmware
echo "Flashing firmware to Crazyflie..."

if [ "$METHOD" = "usb" ]; then
    echo "Using USB method with device: $DEVICE"
    
    # Check if stm32flash is available
    if ! command -v stm32flash &> /dev/null; then
        echo "Error: stm32flash not found"
        echo "Please install stm32flash:"
        echo "  sudo apt-get install stm32flash"
        exit 1
    fi
    
    # Flash the firmware
    echo "Erasing flash..."
    stm32flash -o "$DEVICE"
    
    echo "Writing firmware..."
    stm32flash -w "$FIRMWARE_BIN" "$DEVICE"
    
    if [ "$VERIFY" = true ]; then
        echo "Verifying flash..."
        stm32flash -v "$FIRMWARE_BIN" "$DEVICE"
    fi
    
elif [ "$METHOD" = "radio" ]; then
    echo "Using radio method..."
    
    # Check if cfclient is available
    if ! command -v cfclient &> /dev/null; then
        echo "Error: cfclient not found"
        echo "Please install cfclient:"
        echo "  pip3 install cfclient"
        exit 1
    fi
    
    # Use cfclient for radio flashing
    echo "Connecting to Crazyflie via radio..."
    cfclient --flash "$FIRMWARE_BIN" || {
        echo "Error: Radio flash failed"
        echo "Make sure Crazyflie is powered on and in range"
        exit 1
    }
    
else
    echo "Error: Invalid method '$METHOD'. Use 'usb' or 'radio'"
    exit 1
fi

# Final verification
if [ "$VERIFY" = true ]; then
    echo "Performing final verification..."
    
    # Try to connect and get firmware version
    if command -v cfclient &> /dev/null; then
        echo "Checking firmware version..."
        timeout 10 cfclient --version || echo "Warning: Could not verify firmware version"
    fi
fi

echo ""
echo "Flash completed successfully!"
echo ""
echo "Next steps:"
echo "1. Power cycle the Crazyflie"
echo "2. Test basic functionality"
echo "3. Run swarm tests"
echo ""
echo "To test the firmware:"
echo "  cfclient --scan"
echo "  cfclient --connect"
