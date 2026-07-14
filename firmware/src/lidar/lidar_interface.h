#pragma once

#include "data_types.h"
#include "error_codes.h"

namespace mars_rover::lidar {

class LidarInterface {
 public:
  virtual ~LidarInterface() = default;

  virtual LidarError begin() = 0;
  virtual void end() = 0;
  virtual LidarError reset() = 0;
  virtual LidarError request_device_info() = 0;
  virtual LidarError request_health() = 0;
  virtual LidarError request_supported_scan_modes() = 0;
  virtual LidarError start_scan() = 0;
  virtual LidarError stop_scan() = 0;
  virtual LidarError set_scan_frequency_if_supported(float frequency_hz) = 0;
  virtual LidarError poll(uint32_t now_us) = 0;
  virtual bool read_sample(LidarSample& sample_out) = 0;
  virtual bool read_completed_scan(LidarScan& scan_out) = 0;
  virtual bool is_connected() const = 0;
  virtual bool is_scanning() const = 0;
  virtual LidarError attempt_recovery() = 0;
  virtual LidarError get_last_error() const = 0;
  virtual LidarStatistics get_statistics() const = 0;
};

}  // namespace mars_rover::lidar
