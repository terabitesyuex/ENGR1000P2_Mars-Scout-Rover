#include "openrf1_status.h"

const char *openrf1_status_to_text(OpenRf1Status status) {
    switch (status) {
        case OPENRF1_STATUS_OK:
            return "ok";
        case OPENRF1_STATUS_DISABLED:
            return "disabled";
        case OPENRF1_STATUS_NOT_INITIALIZED:
            return "not_initialized";
        case OPENRF1_STATUS_TIMEOUT:
            return "timeout";
        case OPENRF1_STATUS_NACK:
            return "nack";
        case OPENRF1_STATUS_INVALID_ARGUMENT:
            return "invalid_argument";
        case OPENRF1_STATUS_STALE:
            return "stale";
        case OPENRF1_STATUS_OVERFLOW:
            return "overflow";
        case OPENRF1_STATUS_BAD_ID:
            return "bad_id";
        case OPENRF1_STATUS_HARDWARE_FAULT:
        default:
            return "hardware_fault";
    }
}
