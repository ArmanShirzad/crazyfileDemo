/*
 * Smooth PID Configuration for Crazyflie Swarm Demo
 * 
 * This configuration provides conservative PID settings
 * suitable for smooth, stable flight and precise positioning.
 * 
 * These settings prioritize stability over performance and are
 * recommended for beginners and precision applications.
 */

#ifndef PID_SMOOTH_H
#define PID_SMOOTH_H

// Roll rate PID parameters
#define PID_ROLL_RATE_KP  200.0f
#define PID_ROLL_RATE_KI   25.0f
#define PID_ROLL_RATE_KD    0.0f
#define PID_ROLL_RATE_INTEGRATION_LIMIT  25.0f

// Pitch rate PID parameters
#define PID_PITCH_RATE_KP  200.0f
#define PID_PITCH_RATE_KI   25.0f
#define PID_PITCH_RATE_KD    0.0f
#define PID_PITCH_RATE_INTEGRATION_LIMIT  25.0f

// Yaw rate PID parameters
#define PID_YAW_RATE_KP   100.0f
#define PID_YAW_RATE_KI   10.0f
#define PID_YAW_RATE_KD    0.0f
#define PID_YAW_RATE_INTEGRATION_LIMIT  100.0f

// Roll angle PID parameters
#define PID_ROLL_KP  4.0f
#define PID_ROLL_KI  2.0f
#define PID_ROLL_KD  0.0f
#define PID_ROLL_INTEGRATION_LIMIT  15.0f

// Pitch angle PID parameters
#define PID_PITCH_KP  4.0f
#define PID_PITCH_KI  2.0f
#define PID_PITCH_KD  0.0f
#define PID_PITCH_INTEGRATION_LIMIT  15.0f

// Yaw angle PID parameters
#define PID_YAW_KP  4.0f
#define PID_YAW_KI  0.5f
#define PID_YAW_KD  0.2f
#define PID_YAW_INTEGRATION_LIMIT  180.0f

// Velocity PID parameters (for position control)
#define PID_VEL_X_KP  1.5f
#define PID_VEL_X_KI  0.3f
#define PID_VEL_X_KD  0.0f
#define PID_VEL_X_INTEGRATION_LIMIT  0.8f

#define PID_VEL_Y_KP  1.5f
#define PID_VEL_Y_KI  0.3f
#define PID_VEL_Y_KD  0.0f
#define PID_VEL_Y_INTEGRATION_LIMIT  0.8f

#define PID_VEL_Z_KP  1.5f
#define PID_VEL_Z_KI  0.3f
#define PID_VEL_Z_KD  0.0f
#define PID_VEL_Z_INTEGRATION_LIMIT  0.8f

// Position PID parameters
#define PID_POS_X_KP  0.8f
#define PID_POS_X_KI  0.0f
#define PID_POS_X_KD  0.0f
#define PID_POS_X_INTEGRATION_LIMIT  0.0f

#define PID_POS_Y_KP  0.8f
#define PID_POS_Y_KI  0.0f
#define PID_POS_Y_KD  0.0f
#define PID_POS_Y_INTEGRATION_LIMIT  0.0f

#define PID_POS_Z_KP  0.8f
#define PID_POS_Z_KI  0.0f
#define PID_POS_Z_KD  0.0f
#define PID_POS_Z_INTEGRATION_LIMIT  0.0f

// Altitude hold PID parameters
#define PID_ALT_KP  0.8f
#define PID_ALT_KI  0.0f
#define PID_ALT_KD  0.0f
#define PID_ALT_INTEGRATION_LIMIT  0.0f

// Conservative settings for smooth flight
#define MAX_ROLL_ANGLE_DEG  20.0f
#define MAX_PITCH_ANGLE_DEG 20.0f
#define MAX_YAW_RATE_DEG_S  150.0f
#define MAX_VELOCITY_MS      0.5f
#define MAX_ACCELERATION_MS2 1.0f

// Motor limits for smooth flight
#define MOTOR_PWM_MIN  10000
#define MOTOR_PWM_MAX  50000
#define MOTOR_PWM_DEADBAND 1000

// Safety limits
#define BATTERY_LOW_THRESHOLD_V  3.7f
#define BATTERY_CRITICAL_THRESHOLD_V  3.5f
#define EMERGENCY_LANDING_THRESHOLD_V  3.3f

// Communication settings for swarm
#define RADIO_CHANNEL  80
#define RADIO_DATARATE 2  // 2Mbps
#define RADIO_POWER     0  // Max power
#define SWARM_MAX_DISTANCE_M  30.0f

// Collision avoidance parameters
#define COLLISION_AVOIDANCE_ENABLED  1
#define MIN_SEPARATION_DISTANCE_M    0.5f
#define COLLISION_AVOIDANCE_RANGE_M  1.5f

// Formation flight parameters
#define FORMATION_FLIGHT_ENABLED     1
#define FORMATION_TOLERANCE_M        0.05f
#define FORMATION_MAX_SPEED_MS       0.3f

// Smoothing filters
#define VELOCITY_FILTER_ALPHA  0.8f
#define POSITION_FILTER_ALPHA  0.9f
#define ATTITUDE_FILTER_ALPHA  0.95f

// Rate limiting for smooth control
#define MAX_ROLL_RATE_DEG_S   100.0f
#define MAX_PITCH_RATE_DEG_S  100.0f
#define MAX_YAW_RATE_DEG_S    100.0f

// Dead zones to prevent oscillations
#define ROLL_DEADZONE_DEG     0.5f
#define PITCH_DEADZONE_DEG    0.5f
#define YAW_DEADZONE_DEG      1.0f

#endif // PID_SMOOTH_H
