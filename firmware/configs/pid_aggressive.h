/*
 * Aggressive PID Configuration for Crazyflie Swarm Demo
 * 
 * This configuration provides high-performance PID settings
 * suitable for aggressive flight maneuvers and fast response.
 * 
 * WARNING: These settings may cause instability if not properly tuned
 * for your specific hardware and environment.
 */

#ifndef PID_AGGRESSIVE_H
#define PID_AGGRESSIVE_H

// Roll rate PID parameters
#define PID_ROLL_RATE_KP  250.0f
#define PID_ROLL_RATE_KI   33.0f
#define PID_ROLL_RATE_KD    0.0f
#define PID_ROLL_RATE_INTEGRATION_LIMIT  33.3f

// Pitch rate PID parameters
#define PID_PITCH_RATE_KP  250.0f
#define PID_PITCH_RATE_KI   33.0f
#define PID_PITCH_RATE_KD    0.0f
#define PID_PITCH_RATE_INTEGRATION_LIMIT  33.3f

// Yaw rate PID parameters
#define PID_YAW_RATE_KP   120.0f
#define PID_YAW_RATE_KI   16.7f
#define PID_YAW_RATE_KD    0.0f
#define PID_YAW_RATE_INTEGRATION_LIMIT  166.7f

// Roll angle PID parameters
#define PID_ROLL_KP  6.0f
#define PID_ROLL_KI  3.0f
#define PID_ROLL_KD  0.0f
#define PID_ROLL_INTEGRATION_LIMIT  20.0f

// Pitch angle PID parameters
#define PID_PITCH_KP  6.0f
#define PID_PITCH_KI  3.0f
#define PID_PITCH_KD  0.0f
#define PID_PITCH_INTEGRATION_LIMIT  20.0f

// Yaw angle PID parameters
#define PID_YAW_KP  6.0f
#define PID_YAW_KI  1.0f
#define PID_YAW_KD  0.35f
#define PID_YAW_INTEGRATION_LIMIT  360.0f

// Velocity PID parameters (for position control)
#define PID_VEL_X_KP  2.0f
#define PID_VEL_X_KI  0.5f
#define PID_VEL_X_KD  0.0f
#define PID_VEL_X_INTEGRATION_LIMIT  1.0f

#define PID_VEL_Y_KP  2.0f
#define PID_VEL_Y_KI  0.5f
#define PID_VEL_Y_KD  0.0f
#define PID_VEL_Y_INTEGRATION_LIMIT  1.0f

#define PID_VEL_Z_KP  2.0f
#define PID_VEL_Z_KI  0.5f
#define PID_VEL_Z_KD  0.0f
#define PID_VEL_Z_INTEGRATION_LIMIT  1.0f

// Position PID parameters
#define PID_POS_X_KP  1.0f
#define PID_POS_X_KI  0.0f
#define PID_POS_X_KD  0.0f
#define PID_POS_X_INTEGRATION_LIMIT  0.0f

#define PID_POS_Y_KP  1.0f
#define PID_POS_Y_KI  0.0f
#define PID_POS_Y_KD  0.0f
#define PID_POS_Y_INTEGRATION_LIMIT  0.0f

#define PID_POS_Z_KP  1.0f
#define PID_POS_Z_KI  0.0f
#define PID_POS_Z_KD  0.0f
#define PID_POS_Z_INTEGRATION_LIMIT  0.0f

// Altitude hold PID parameters
#define PID_ALT_KP  1.0f
#define PID_ALT_KI  0.0f
#define PID_ALT_KD  0.0f
#define PID_ALT_INTEGRATION_LIMIT  0.0f

// Additional aggressive settings
#define MAX_ROLL_ANGLE_DEG  30.0f
#define MAX_PITCH_ANGLE_DEG 30.0f
#define MAX_YAW_RATE_DEG_S  200.0f
#define MAX_VELOCITY_MS      1.0f
#define MAX_ACCELERATION_MS2 2.0f

// Motor limits for aggressive flight
#define MOTOR_PWM_MIN  10000
#define MOTOR_PWM_MAX  60000
#define MOTOR_PWM_DEADBAND 1000

// Safety limits
#define BATTERY_LOW_THRESHOLD_V  3.7f
#define BATTERY_CRITICAL_THRESHOLD_V  3.5f
#define EMERGENCY_LANDING_THRESHOLD_V  3.3f

// Communication settings for swarm
#define RADIO_CHANNEL  80
#define RADIO_DATARATE 2  // 2Mbps
#define RADIO_POWER     0  // Max power
#define SWARM_MAX_DISTANCE_M  50.0f

// Collision avoidance parameters
#define COLLISION_AVOIDANCE_ENABLED  1
#define MIN_SEPARATION_DISTANCE_M    0.3f
#define COLLISION_AVOIDANCE_RANGE_M  2.0f

// Formation flight parameters
#define FORMATION_FLIGHT_ENABLED     1
#define FORMATION_TOLERANCE_M        0.1f
#define FORMATION_MAX_SPEED_MS       0.5f

#endif // PID_AGGRESSIVE_H
