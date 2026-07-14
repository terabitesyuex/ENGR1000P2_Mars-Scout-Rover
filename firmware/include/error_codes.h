#pragma once

#include <cstdint>

namespace mars_rover::lidar {

enum class LidarError : uint8_t {
  kOk = 0,
  kNotInitialized,
  kInvalidArgument,
  kSerialOpenFailed,
  kSerialWriteFailed,
  kSerialReadFailed,
  kResponseTimeout,
  kInvalidResponseHeader,
  kInvalidResponseLength,
  kChecksumError,
  kUnsupportedResponseType,
  kUnsupportedScanMode,
  kDeviceHealthError,
  kRxBufferOverflow,
  kPcTransportCongestion,
  kRecoveryFailed,
};

constexpr bool is_ok(const LidarError error) {
  return error == LidarError::kOk;
}

}  // namespace mars_rover::lidar
