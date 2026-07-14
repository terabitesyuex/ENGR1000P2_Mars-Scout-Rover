#pragma once

#include <cstdint>

#include "app/system_state.h"

namespace mars_rover::lidar::app {

class LidarApplication {
 public:
  void begin() noexcept;
  void poll(uint32_t now_ms) noexcept;
  SystemState state() const noexcept;

 private:
  SystemState state_ = SystemState::kBoot;
};

}  // namespace mars_rover::lidar::app
