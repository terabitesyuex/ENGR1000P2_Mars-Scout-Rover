#pragma once

#include "lidar/lidar_interface.h"

namespace mars_rover::lidar {

class C1Driver final : public LidarInterface {
 public:
  LidarError begin() override;
  void end() override;
  LidarError reset() override;
  LidarError request_device_info() override;
  LidarError request_health() override;
  LidarError request_supported_scan_modes() override;
  LidarError start_scan() override;
  LidarError stop_scan() override;
  LidarError set_scan_frequency_if_supported(float frequency_hz) override;
  LidarError poll(uint32_t now_us) override;
  bool read_sample(LidarSample& sample_out) override;
  bool read_completed_scan(LidarScan& scan_out) override;
  bool is_connected() const override;
  bool is_scanning() const override;
  LidarError attempt_recovery() override;
  LidarError get_last_error() const override;
  LidarStatistics get_statistics() const override;

 private:
  LidarError last_error_ = LidarError::kNotInitialized;
  LidarStatistics statistics_ = {};
};

}  // namespace mars_rover::lidar
