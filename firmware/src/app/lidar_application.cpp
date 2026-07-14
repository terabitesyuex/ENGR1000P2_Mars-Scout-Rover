#include "app/lidar_application.h"

namespace mars_rover::lidar::app {

void LidarApplication::begin() noexcept {
  state_ = SystemState::kHardwareCheck;
}

void LidarApplication::poll(const uint32_t /*now_ms*/) noexcept {
  // Phase 0 does not perform hardware actions.
}

SystemState LidarApplication::state() const noexcept {
  return state_;
}

}  // namespace mars_rover::lidar::app
