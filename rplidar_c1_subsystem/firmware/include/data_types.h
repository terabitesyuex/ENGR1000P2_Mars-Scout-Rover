#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

#include "app_config.h"

namespace mars_rover::lidar {

struct LidarDeviceInfo {
  uint8_t model_identifier = 0;
  uint8_t firmware_major = 0;
  uint8_t firmware_minor = 0;
  uint8_t hardware_revision = 0;
  char redacted_serial_identifier[9] = {};
  bool valid = false;
};

struct LidarHealth {
  uint8_t health_state = 0;
  uint16_t device_error_code = 0;
  uint32_t timestamp_ms = 0;
  bool valid = false;
};

struct RawLidarSample {
  uint32_t timestamp_us = 0;
  uint32_t scan_id = 0;
  uint16_t raw_angle_value = 0;
  uint16_t raw_distance_value = 0;
  uint16_t raw_quality_or_reflectivity = 0;
  bool scan_start = false;
  bool protocol_valid = false;
};

struct LidarSample {
  uint32_t timestamp_us = 0;
  uint32_t scan_id = 0;
  float angle_clockwise_deg = 0.0F;
  float angle_robot_deg = 0.0F;
  uint16_t distance_mm = 0;
  uint16_t reflectivity_raw = 0;
  bool scan_start = false;
  bool protocol_valid = false;
  bool range_valid = false;
  bool quality_valid = false;
  bool filter_valid = false;
};

struct LidarScan {
  uint32_t scan_id = 0;
  uint32_t start_timestamp_us = 0;
  uint32_t end_timestamp_us = 0;
  std::array<LidarSample, config::kMaximumSamplesPerScan> samples = {};
  std::size_t received_point_count = 0;
  std::size_t valid_point_count = 0;
  std::size_t rejected_point_count = 0;
  float estimated_scan_frequency_hz = 0.0F;
  bool complete = false;
};

struct LidarStatistics {
  uint32_t total_bytes = 0;
  uint32_t total_samples = 0;
  uint32_t valid_samples = 0;
  uint32_t rejected_samples = 0;
  uint32_t completed_scans = 0;
  uint32_t parser_errors = 0;
  uint32_t checksum_errors = 0;
  uint32_t timeouts = 0;
  uint32_t overflow_count = 0;
  uint32_t recovery_count = 0;
};

}  // namespace mars_rover::lidar
