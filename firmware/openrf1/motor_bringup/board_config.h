#pragma once

#include <stdint.h>

#define OPENRF1_MOTOR_BRINGUP_BOARD "OpenRF1_STM32F103RCT6"
#define OPENRF1_MOTOR_BRINGUP_MAPPING_STATUS \
    "vendor_connector_mapping_physical_wheels_unverified"
#define OPENRF1_MOTOR_BRINGUP_USART_BAUD ((uint32_t)115200u)
#define OPENRF1_MOTOR_BRINGUP_PWM_PRESCALER ((uint16_t)71u)
#define OPENRF1_MOTOR_BRINGUP_PWM_AUTO_RELOAD ((uint16_t)999u)
#define OPENRF1_MOTOR_BRINGUP_STATUS_PERIOD_MS ((uint32_t)100u)
#define OPENRF1_MOTOR_BRINGUP_COMMAND_BUFFER_BYTES ((uint16_t)96u)
#define OPENRF1_MOTOR_BRINGUP_TX_BUFFER_BYTES ((uint16_t)1024u)
#define OPENRF1_MOTOR_BRINGUP_RX_BUFFER_BYTES ((uint16_t)128u)
#define OPENRF1_MOTOR_BRINGUP_TELEMETRY_BUFFER_BYTES ((uint16_t)768u)

/*
 * This is a representation bound, not a verified safe physical duty.
 * Runtime configuration must explicitly choose a lower reviewed ceiling.
 */
#define OPENRF1_MOTOR_BRINGUP_DUTY_REPRESENTATION_MAX ((uint16_t)1000u)
#define OPENRF1_MOTOR_BRINGUP_WATCHDOG_REPRESENTATION_MAX_MS ((uint32_t)10000u)

