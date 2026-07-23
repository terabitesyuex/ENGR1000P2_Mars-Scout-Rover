#pragma once

#include <stdint.h>

/*
 * Unified rover-control hardware contract.
 *
 * Values marked UNKNOWN must stay unusable until an authoritative OpenRF1
 * schematic, connector definition, or controlled measurement resolves them.
 * Pure control modules must accept geometry and hardware backends at runtime;
 * they must not replace these sentinels with guessed GPIO assignments.
 */
#define OPENRF1_HARDWARE_UNKNOWN_I32 ((int32_t)-1)
#define OPENRF1_HARDWARE_UNKNOWN_U32 UINT32_MAX
#define OPENRF1_HARDWARE_UNKNOWN_TEXT "UNKNOWN"

#define OPENRF1_ROVER_MOTOR_COUNT ((uint8_t)4u)
#define OPENRF1_ROVER_ENCODER_COUNT ((uint8_t)4u)

/* Task input for software configuration; physical integration is UNVERIFIED. */
#define OPENRF1_JGB37_520_MIN_SUPPLY_MV ((uint32_t)6000u)
#define OPENRF1_JGB37_520_MAX_SUPPLY_MV ((uint32_t)12000u)
#define OPENRF1_ENCODER_MOTOR_SHAFT_PPR ((uint32_t)11u)
#define OPENRF1_GEAR_RATIO_NUMERATOR ((uint32_t)30u)
#define OPENRF1_GEAR_RATIO_DENOMINATOR ((uint32_t)1u)
#define OPENRF1_ENCODER_OUTPUT_SHAFT_PPR ((uint32_t)330u)
#define OPENRF1_ENCODER_QUADRATURE_MULTIPLIER ((uint32_t)4u)
#define OPENRF1_ENCODER_COUNTS_PER_OUTPUT_REV ((uint32_t)1320u)

/*
 * User-supplied as-built geometry, stored at 0.1 mm resolution so the 39.5 mm
 * wheel radius and 108.5 mm half-track are not rounded. The current mecanum API
 * accepts whole millimetres, so its legacy fields stay disabled until a
 * deliberate conversion/precision contract is implemented.
 */
#define OPENRF1_WHEEL_DIAMETER_X10_MM ((uint32_t)790u)
#define OPENRF1_WHEELBASE_X10_MM ((uint32_t)1900u)
#define OPENRF1_TRACK_WIDTH_X10_MM ((uint32_t)2170u)
#define OPENRF1_RPLIDAR_C1_SCAN_PLANE_HEIGHT_ABOVE_CHASSIS_X10_MM ((uint32_t)858u)

/* Runtime geometry remains fail-disabled pending signs and precision policy. */
#define OPENRF1_WHEEL_RADIUS_MM OPENRF1_HARDWARE_UNKNOWN_I32
#define OPENRF1_HALF_WHEELBASE_MM OPENRF1_HARDWARE_UNKNOWN_I32
#define OPENRF1_HALF_TRACK_WIDTH_MM OPENRF1_HARDWARE_UNKNOWN_I32
#define OPENRF1_MAX_WHEEL_SPEED_MRAD_S OPENRF1_HARDWARE_UNKNOWN_I32
#define OPENRF1_MECANUM_ROLLER_LAYOUT OPENRF1_HARDWARE_UNKNOWN_I32
#define OPENRF1_MECANUM_GEOMETRY_READY ((uint8_t)0u)

/*
 * Vendor-documented electrical mappings. Logical wheel assignment follows the
 * assembly design and still requires CN-to-wheel trace confirmation.
 */
#define OPENRF1_MOTOR_FRONT_LEFT_CONNECTOR "CN2"
#define OPENRF1_MOTOR_FRONT_LEFT_PWM_PIN "PC7/TIM8_CH2"
#define OPENRF1_MOTOR_FRONT_LEFT_DIRECTION_PIN "PA11"
#define OPENRF1_MOTOR_FRONT_RIGHT_CONNECTOR "CN4"
#define OPENRF1_MOTOR_FRONT_RIGHT_PWM_PIN "PC9/TIM8_CH4"
#define OPENRF1_MOTOR_FRONT_RIGHT_DIRECTION_PIN "PC10"
#define OPENRF1_MOTOR_REAR_LEFT_CONNECTOR "CN1"
#define OPENRF1_MOTOR_REAR_LEFT_PWM_PIN "PC6/TIM8_CH1"
#define OPENRF1_MOTOR_REAR_LEFT_DIRECTION_PIN "PA8"
#define OPENRF1_MOTOR_REAR_RIGHT_CONNECTOR "CN3"
#define OPENRF1_MOTOR_REAR_RIGHT_PWM_PIN "PC8/TIM8_CH3"
#define OPENRF1_MOTOR_REAR_RIGHT_DIRECTION_PIN "PA12"
#define OPENRF1_MOTOR_PWM_TIMER "TIM8"
#define OPENRF1_MOTOR_ENABLE_SIGNAL OPENRF1_HARDWARE_UNKNOWN_TEXT
#define OPENRF1_MOTOR_BRAKE_BEHAVIOR OPENRF1_HARDWARE_UNKNOWN_TEXT

/* Vendor-documented encoder channels; physical signs remain unknown. */
#define OPENRF1_ENCODER_FRONT_LEFT_A_PIN "PA6"
#define OPENRF1_ENCODER_FRONT_LEFT_B_PIN "PA7"
#define OPENRF1_ENCODER_FRONT_RIGHT_A_PIN "PB6"
#define OPENRF1_ENCODER_FRONT_RIGHT_B_PIN "PB7"
#define OPENRF1_ENCODER_REAR_LEFT_A_PIN "PA0"
#define OPENRF1_ENCODER_REAR_LEFT_B_PIN "PA1"
#define OPENRF1_ENCODER_REAR_RIGHT_A_PIN "PA15"
#define OPENRF1_ENCODER_REAR_RIGHT_B_PIN "PB3"
#define OPENRF1_ENCODER_TIMER_MAPPING "FL=TIM3,FR=TIM4,RL=TIM5,RR=TIM2_FULL_REMAP"
#define OPENRF1_ENCODER_DIRECTION_SIGNS OPENRF1_HARDWARE_UNKNOWN_TEXT

/* Vendor-documented UART routing; physical links remain unverified. */
#define OPENRF1_RPLIDAR_C1_UART "USART2"
#define OPENRF1_RPLIDAR_C1_UART_TX_PIN "PA2"
#define OPENRF1_RPLIDAR_C1_UART_RX_PIN "PA3"
#define OPENRF1_ESP32_UART "USART3"
#define OPENRF1_ESP32_UART_TX_PIN "PB10"
#define OPENRF1_ESP32_UART_RX_PIN "PB11"

#define OPENRF1_MOTOR_HARDWARE_MAPPING_READY ((uint8_t)0u)
#define OPENRF1_ENCODER_HARDWARE_MAPPING_READY ((uint8_t)0u)
#define OPENRF1_RPLIDAR_C1_UART_MAPPING_READY ((uint8_t)0u)
#define OPENRF1_ESP32_UART_MAPPING_READY ((uint8_t)0u)
