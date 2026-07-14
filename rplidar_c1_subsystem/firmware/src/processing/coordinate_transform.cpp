#include "processing/coordinate_transform.h"

#include <cmath>

namespace mars_rover::lidar::processing {

float normalize_angle_deg(float angle_deg) {
  float normalized = std::fmod(angle_deg, 360.0F);
  if (normalized < 0.0F) {
    normalized += 360.0F;
  }
  if (std::fabs(normalized - 360.0F) < 0.0001F) {
    return 0.0F;
  }
  return normalized;
}

float native_clockwise_to_robot_angle_deg(const float native_clockwise_angle_deg) {
  return normalize_angle_deg(-native_clockwise_angle_deg);
}

}  // namespace mars_rover::lidar::processing
