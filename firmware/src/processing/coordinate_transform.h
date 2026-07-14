#pragma once

namespace mars_rover::lidar::processing {

float normalize_angle_deg(float angle_deg);
float native_clockwise_to_robot_angle_deg(float native_clockwise_angle_deg);

}  // namespace mars_rover::lidar::processing
