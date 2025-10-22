# Crazyflie Firmware Build Guide

This directory contains scripts and documentation for building and flashing Crazyflie firmware.

## Overview

The Crazyflie 2.1 uses an STM32F405 microcontroller running FreeRTOS. This guide covers building the official crazyflie-firmware with custom configurations for swarm applications.

## Prerequisites

### Option 1: Docker (Recommended)
- Docker installed on your system
- No additional toolchain setup required

### Option 2: Native ARM Toolchain
- ARM GCC toolchain (arm-none-eabi-gcc)
- Make
- Git

## Quick Start

### Using Docker
```bash
cd firmware
./build.sh
./flash.sh /dev/ttyUSB0
```

### Using Native Toolchain
```bash
cd firmware
./setup.sh
./build.sh
./flash.sh /dev/ttyUSB0
```

## Build Scripts

### setup.sh
Installs the ARM GCC toolchain and dependencies:
- Downloads and installs arm-none-eabi-gcc
- Sets up environment variables
- Installs required Python packages

### build.sh
Builds the crazyflie-firmware:
- Clones the official firmware repository
- Applies custom configurations
- Compiles firmware with optimizations
- Generates binary files

### flash.sh
Flashes firmware to Crazyflie:
- Connects to Crazyflie via USB or radio
- Erases flash memory
- Writes new firmware
- Verifies flash operation

## Configuration Files

### configs/pid_aggressive.h
High-performance PID settings for aggressive flight:
```c
#define PID_ROLL_RATE_KP  250.0f
#define PID_ROLL_RATE_KI   33.0f
#define PID_ROLL_RATE_KD    0.0f
#define PID_ROLL_RATE_INTEGRATION_LIMIT  33.3f
```

### configs/pid_smooth.h
Conservative PID settings for smooth flight:
```c
#define PID_ROLL_RATE_KP  200.0f
#define PID_ROLL_RATE_KI   25.0f
#define PID_ROLL_RATE_KD    0.0f
#define PID_ROLL_RATE_INTEGRATION_LIMIT  25.0f
```

## Customization

### PID Tuning
1. Edit `controller_pid.c` in the firmware source
2. Modify PID gains for your specific use case
3. Rebuild and test with single drone first
4. Test with swarm after validation

### Communication Parameters
- Radio frequency: 2.4GHz
- Channel: Configurable (default 80)
- Data rate: 2Mbps
- Range: ~100m line of sight

### Safety Limits
- Maximum velocity: 1.0 m/s
- Maximum acceleration: 2.0 m/s²
- Battery low threshold: 3.7V
- Emergency stop: Immediate motor cut

## Troubleshooting

### Common Issues

#### Build Errors
- **Error**: "arm-none-eabi-gcc not found"
  - **Solution**: Run `./setup.sh` or use Docker

- **Error**: "Makefile not found"
  - **Solution**: Ensure you're in the firmware directory

#### Flash Errors
- **Error**: "Device not found"
  - **Solution**: Check USB connection and permissions
  - **Solution**: Try different USB port

- **Error**: "Flash verification failed"
  - **Solution**: Retry flash operation
  - **Solution**: Check battery level (>3.7V)

#### Runtime Issues
- **Issue**: Drone not responding to commands
  - **Solution**: Check radio connection
  - **Solution**: Verify firmware version

- **Issue**: Unstable flight
  - **Solution**: Tune PID parameters
  - **Solution**: Check propeller condition

### Debug Tools

#### Serial Monitor
```bash
# Monitor serial output
screen /dev/ttyUSB0 115200
```

#### Radio Sniffer
```bash
# Use Crazyflie client tools
cfclient --scan
```

## Performance Optimization

### Compiler Flags
- `-O2`: Optimize for performance
- `-Os`: Optimize for size
- `-ffast-math`: Enable fast math operations

### Memory Management
- Stack size: 4KB per task
- Heap size: 32KB
- Flash usage: ~200KB

### Real-time Constraints
- Control loop: 1kHz
- Sensor fusion: 500Hz
- Communication: 100Hz

## Testing

### Unit Tests
```bash
# Run firmware unit tests
make test
```

### Hardware-in-the-Loop
```bash
# Test with simulator
make test_hil
```

### Swarm Testing
1. Flash firmware to all drones
2. Test individual drone functionality
3. Test communication between drones
4. Test swarm coordination algorithms

## Advanced Features

### Custom Parameters
Add new parameters to `param.h`:
```c
PARAM_GROUP_START(custom)
PARAM_ADD(PARAM_UINT8, my_param, &my_param)
PARAM_GROUP_STOP(custom)
```

### Custom Commands
Add commands to `commander.c`:
```c
static void customCommand(const uint8_t* data)
{
    // Custom command implementation
}
```

### Sensor Integration
- IMU: STM32F405 built-in
- Barometer: LPS25H
- Optical flow: PMW3901 (optional)

## References

- [Crazyflie Firmware Repository](https://github.com/bitcraze/crazyflie-firmware)
- [STM32F405 Reference Manual](https://www.st.com/resource/en/reference_manual/dm00031020.pdf)
- [FreeRTOS Documentation](https://www.freertos.org/Documentation/)
- [Crazyflie Hardware Documentation](https://www.bitcraze.io/documentation/)

## Support

For issues specific to this demo:
1. Check the troubleshooting section above
2. Review the main project documentation
3. Open an issue in the project repository

For general Crazyflie issues:
- [Bitcraze Forum](https://forum.bitcraze.io/)
- [Crazyflie Documentation](https://www.bitcraze.io/documentation/)
