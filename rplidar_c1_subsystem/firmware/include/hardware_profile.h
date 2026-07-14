#pragma once

#include <Arduino.h>
#include <cstdint>

namespace mars_rover::lidar::hardware {

constexpr uint32_t kLidarBaudRate = 460800;
constexpr uint32_t kLidarSerialConfig = SERIAL_8N1;

#ifndef RPLIDAR_C1_LIDAR_RX_PIN
#error "Set RPLIDAR_C1_LIDAR_RX_PIN only after verifying the ESP32-C3 SuperMini RX GPIO."
#endif

#ifndef RPLIDAR_C1_LIDAR_TX_PIN
#error "Set RPLIDAR_C1_LIDAR_TX_PIN only after verifying the ESP32-C3 SuperMini TX GPIO."
#endif

constexpr int kLidarRxPin = RPLIDAR_C1_LIDAR_RX_PIN;
constexpr int kLidarTxPin = RPLIDAR_C1_LIDAR_TX_PIN;

constexpr bool kHasExternalMotorPwm = false;
constexpr float kLidarNominalVoltageV = 5.0F;
constexpr uint32_t kLidarStartupCurrentMa = 800;
constexpr uint32_t kLidarTypicalOperatingCurrentMa = 230;
constexpr uint32_t kLidarMaximumNormalOperatingCurrentMa = 260;

}  // namespace mars_rover::lidar::hardware
