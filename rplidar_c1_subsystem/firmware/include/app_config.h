#pragma once

#include <cstddef>
#include <cstdint>

namespace mars_rover::lidar::config {

constexpr uint16_t kMinimumUsefulRangeMm = 50;
constexpr uint16_t kMaximumUsefulRangeMm = 12000;
constexpr std::size_t kMaximumSamplesPerScan = 720;
constexpr uint32_t kExpectedScanFrequencyHz = 10;
constexpr uint32_t kMaximumScanDurationMs = 250;
constexpr uint32_t kMinimumCompleteScanPoints = 120;

}  // namespace mars_rover::lidar::config
