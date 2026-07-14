#pragma once

#include <cstdint>

namespace mars_rover::lidar::app {

enum class SystemState : uint8_t {
  kBoot,
  kHardwareCheck,
  kSerialInitialising,
  kLidarResetting,
  kLidarIdentifying,
  kLidarHealthCheck,
  kIdle,
  kStartingScan,
  kScanning,
  kStoppingScan,
  kRecovering,
  kDegraded,
  kFault,
};

}  // namespace mars_rover::lidar::app
