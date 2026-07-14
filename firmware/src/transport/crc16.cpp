#include "transport/crc16.h"

namespace mars_rover::lidar::transport {

uint16_t crc16_ccitt_false(const uint8_t* data, const std::size_t length) {
  uint16_t crc = 0xFFFF;
  for (std::size_t index = 0; index < length; ++index) {
    crc ^= static_cast<uint16_t>(data[index]) << 8U;
    for (uint8_t bit = 0; bit < 8U; ++bit) {
      if ((crc & 0x8000U) != 0U) {
        crc = static_cast<uint16_t>((crc << 1U) ^ 0x1021U);
      } else {
        crc = static_cast<uint16_t>(crc << 1U);
      }
    }
  }
  return crc;
}

}  // namespace mars_rover::lidar::transport
