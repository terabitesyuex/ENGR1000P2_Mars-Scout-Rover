#pragma once

#include <stdint.h>

typedef enum {
    MECANUM_STATUS_OK = 0,
    MECANUM_STATUS_INVALID_ARGUMENT,
    MECANUM_STATUS_INVALID_GEOMETRY,
    MECANUM_STATUS_RESULT_OUT_OF_RANGE
} MecanumStatus;

typedef enum {
    MECANUM_ROLLER_LAYOUT_UNVERIFIED = 0,
    MECANUM_ROLLER_LAYOUT_X = 1
} MecanumRollerLayout;

typedef struct {
    uint32_t wheel_radius_mm;
    uint32_t half_wheelbase_mm;
    uint32_t half_track_width_mm;
    int32_t max_wheel_speed_mrad_s;
    MecanumRollerLayout roller_layout;
} MecanumGeometry;

typedef struct {
    int32_t vx_mm_s;
    int32_t vy_mm_s;
    int32_t omega_mrad_s;
} MecanumBodyVelocity;

typedef struct {
    int32_t front_left_mrad_s;
    int32_t front_right_mrad_s;
    int32_t rear_left_mrad_s;
    int32_t rear_right_mrad_s;
} MecanumWheelSpeeds;

MecanumStatus mecanum_validate_geometry(const MecanumGeometry *geometry);
MecanumStatus mecanum_inverse_kinematics(
    const MecanumGeometry *geometry,
    const MecanumBodyVelocity *body_velocity,
    MecanumWheelSpeeds *wheel_speeds
);
