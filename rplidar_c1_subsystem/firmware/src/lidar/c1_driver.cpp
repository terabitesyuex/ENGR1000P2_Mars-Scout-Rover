#include "lidar/c1_driver.h"

namespace mars_rover::lidar {

LidarError C1Driver::begin() {
  last_error_ = LidarError::kNotInitialized;
  return last_error_;
}

void C1Driver::end() {}

LidarError C1Driver::reset() {
  return LidarError::kNotInitialized;
}

LidarError C1Driver::request_device_info() {
  return LidarError::kNotInitialized;
}

LidarError C1Driver::request_health() {
  return LidarError::kNotInitialized;
}

LidarError C1Driver::request_supported_scan_modes() {
  return LidarError::kNotInitialized;
}

LidarError C1Driver::start_scan() {
  return LidarError::kNotInitialized;
}

LidarError C1Driver::stop_scan() {
  return LidarError::kNotInitialized;
}

LidarError C1Driver::set_scan_frequency_if_supported(const float /*frequency_hz*/) {
  return LidarError::kUnsupportedScanMode;
}

LidarError C1Driver::poll(const uint32_t /*now_us*/) {
  return LidarError::kNotInitialized;
}

bool C1Driver::read_sample(LidarSample& /*sample_out*/) {
  return false;
}

bool C1Driver::read_completed_scan(LidarScan& /*scan_out*/) {
  return false;
}

bool C1Driver::is_connected() const {
  return false;
}

bool C1Driver::is_scanning() const {
  return false;
}

LidarError C1Driver::attempt_recovery() {
  ++statistics_.recovery_count;
  last_error_ = LidarError::kRecoveryFailed;
  return last_error_;
}

LidarError C1Driver::get_last_error() const {
  return last_error_;
}

LidarStatistics C1Driver::get_statistics() const {
  return statistics_;
}

}  // namespace mars_rover::lidar
