#include "mecanum.h"

#include <limits.h>

#define MECANUM_MAX_GEOMETRY_DIMENSION_MM ((uint32_t)1000000u)

static int64_t divide_round_nearest(int64_t numerator, int64_t denominator) {
    if (numerator >= 0) {
        return (numerator + denominator / 2) / denominator;
    }
    return -((-numerator + denominator / 2) / denominator);
}

static uint8_t int64_fits_int32(int64_t value) {
    return (uint8_t)(value >= (int64_t)INT32_MIN && value <= (int64_t)INT32_MAX);
}

static int64_t absolute_int32_as_int64(int32_t value) {
    if (value < 0) {
        return -(int64_t)value;
    }
    return (int64_t)value;
}

MecanumStatus mecanum_validate_geometry(const MecanumGeometry *geometry) {
    if (geometry == 0) {
        return MECANUM_STATUS_INVALID_ARGUMENT;
    }
    if (geometry->wheel_radius_mm == 0u ||
        geometry->half_wheelbase_mm == 0u ||
        geometry->half_track_width_mm == 0u ||
        geometry->max_wheel_speed_mrad_s <= 0 ||
        geometry->roller_layout != MECANUM_ROLLER_LAYOUT_X) {
        return MECANUM_STATUS_INVALID_GEOMETRY;
    }
    if (geometry->wheel_radius_mm > MECANUM_MAX_GEOMETRY_DIMENSION_MM ||
        geometry->half_wheelbase_mm > MECANUM_MAX_GEOMETRY_DIMENSION_MM ||
        geometry->half_track_width_mm > MECANUM_MAX_GEOMETRY_DIMENSION_MM) {
        return MECANUM_STATUS_INVALID_GEOMETRY;
    }
    return MECANUM_STATUS_OK;
}

MecanumStatus mecanum_inverse_kinematics(
    const MecanumGeometry *geometry,
    const MecanumBodyVelocity *body_velocity,
    MecanumWheelSpeeds *wheel_speeds
) {
    int64_t lever_arm_mm;
    int64_t rotation_linear_mm_s;
    int64_t wheel_linear_mm_s[4];
    int64_t wheel_angular_mrad_s[4];
    int64_t max_absolute_speed = 0;
    int64_t speed_limit;
    uint8_t index;
    MecanumStatus status;

    if (body_velocity == 0 || wheel_speeds == 0) {
        return MECANUM_STATUS_INVALID_ARGUMENT;
    }
    status = mecanum_validate_geometry(geometry);
    if (status != MECANUM_STATUS_OK) {
        return status;
    }

    lever_arm_mm =
        (int64_t)geometry->half_wheelbase_mm +
        (int64_t)geometry->half_track_width_mm;
    rotation_linear_mm_s = divide_round_nearest(
        (int64_t)body_velocity->omega_mrad_s * lever_arm_mm,
        1000
    );

    /*
     * Rover frame: +x forward, +y left, +omega counterclockwise.
     * Logical wheel ordering is independent of connector and motor polarity.
     */
    wheel_linear_mm_s[0] =
        (int64_t)body_velocity->vx_mm_s -
        (int64_t)body_velocity->vy_mm_s -
        rotation_linear_mm_s;
    wheel_linear_mm_s[1] =
        (int64_t)body_velocity->vx_mm_s +
        (int64_t)body_velocity->vy_mm_s +
        rotation_linear_mm_s;
    wheel_linear_mm_s[2] =
        (int64_t)body_velocity->vx_mm_s +
        (int64_t)body_velocity->vy_mm_s -
        rotation_linear_mm_s;
    wheel_linear_mm_s[3] =
        (int64_t)body_velocity->vx_mm_s -
        (int64_t)body_velocity->vy_mm_s +
        rotation_linear_mm_s;

    for (index = 0u; index < 4u; ++index) {
        int64_t absolute_speed;

        wheel_angular_mrad_s[index] = divide_round_nearest(
            wheel_linear_mm_s[index] * 1000,
            (int64_t)geometry->wheel_radius_mm
        );
        if (!int64_fits_int32(wheel_angular_mrad_s[index])) {
            return MECANUM_STATUS_RESULT_OUT_OF_RANGE;
        }
        absolute_speed = absolute_int32_as_int64((int32_t)wheel_angular_mrad_s[index]);
        if (absolute_speed > max_absolute_speed) {
            max_absolute_speed = absolute_speed;
        }
    }

    speed_limit = (int64_t)geometry->max_wheel_speed_mrad_s;
    if (max_absolute_speed > speed_limit) {
        for (index = 0u; index < 4u; ++index) {
            wheel_angular_mrad_s[index] = divide_round_nearest(
                wheel_angular_mrad_s[index] * speed_limit,
                max_absolute_speed
            );
        }
    }

    wheel_speeds->front_left_mrad_s = (int32_t)wheel_angular_mrad_s[0];
    wheel_speeds->front_right_mrad_s = (int32_t)wheel_angular_mrad_s[1];
    wheel_speeds->rear_left_mrad_s = (int32_t)wheel_angular_mrad_s[2];
    wheel_speeds->rear_right_mrad_s = (int32_t)wheel_angular_mrad_s[3];
    return MECANUM_STATUS_OK;
}
