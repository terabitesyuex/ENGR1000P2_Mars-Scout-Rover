#pragma once

#include <cstddef>
#include <cstdint>

namespace mars_rover::lidar::transport {

uint16_t crc16_ccitt_false(const uint8_t* data, std::size_t length);

}  // namespace mars_rover::lidar::transport
