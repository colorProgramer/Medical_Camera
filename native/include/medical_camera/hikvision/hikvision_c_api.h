#pragma once

#include <stdint.h>

#ifdef _WIN32
#  ifdef MEDICAL_CAMERA_HIKVISION_CAPI_EXPORTS
#    define MC_HIK_API __declspec(dllexport)
#  else
#    define MC_HIK_API __declspec(dllimport)
#  endif
#else
#  define MC_HIK_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct mc_hik_device_info_t {
    uint32_t index;
    uint32_t transport_layer_type;
    char vendor_name[64];
    char model_name[64];
    char serial_number[64];
    char user_defined_name[64];
    char ip_address[32];
} mc_hik_device_info_t;

typedef struct mc_hik_int_node_t {
    int status;
    int64_t current;
    int64_t minimum;
    int64_t maximum;
    int64_t increment;
} mc_hik_int_node_t;

typedef struct mc_hik_float_node_t {
    int status;
    float current;
    float minimum;
    float maximum;
} mc_hik_float_node_t;

typedef struct mc_hik_enum_node_t {
    int status;
    uint32_t current;
    uint32_t supported_count;
    uint32_t supported_values[256];
} mc_hik_enum_node_t;

typedef struct mc_hik_bool_node_t {
    int status;
    int current;
} mc_hik_bool_node_t;

typedef struct mc_hik_string_node_t {
    int status;
    char current[256];
} mc_hik_string_node_t;

typedef struct mc_hik_snapshot_t {
    mc_hik_int_node_t width;
    mc_hik_int_node_t height;
    mc_hik_int_node_t payload_size;

    mc_hik_float_node_t exposure_time;
    mc_hik_float_node_t gain;
    mc_hik_float_node_t frame_rate;

    mc_hik_enum_node_t pixel_format;
    mc_hik_enum_node_t exposure_auto;
    mc_hik_enum_node_t gain_auto;
    mc_hik_enum_node_t white_balance_auto;
    mc_hik_enum_node_t balance_ratio_selector;
    mc_hik_enum_node_t trigger_mode;
    mc_hik_enum_node_t trigger_source;

    mc_hik_int_node_t balance_ratio_red;
    mc_hik_int_node_t balance_ratio_green;
    mc_hik_int_node_t balance_ratio_blue;

    mc_hik_bool_node_t reverse_x;
    mc_hik_bool_node_t reverse_y;
    mc_hik_string_node_t device_user_id;

    int optimal_packet_size_status;
    uint32_t optimal_packet_size;
} mc_hik_snapshot_t;

typedef struct mc_hik_frame_info_t {
    int status;
    uint32_t width;
    uint32_t height;
    uint32_t frame_number;
    uint32_t pixel_type;
    uint32_t byte_count;
} mc_hik_frame_info_t;

MC_HIK_API int mc_hik_initialize(void);
MC_HIK_API int mc_hik_finalize(void);
MC_HIK_API int mc_hik_enumerate_devices(uint32_t transport_layer_mask, mc_hik_device_info_t* devices, uint32_t capacity, uint32_t* out_count);
MC_HIK_API void* mc_hik_create_camera(void);
MC_HIK_API void mc_hik_destroy_camera(void* camera);
MC_HIK_API int mc_hik_open_by_index(void* camera, uint32_t device_index, uint32_t transport_layer_mask);
MC_HIK_API int mc_hik_close(void* camera);
MC_HIK_API int mc_hik_is_connected(void* camera);
MC_HIK_API int mc_hik_query_snapshot(void* camera, mc_hik_snapshot_t* snapshot);
MC_HIK_API int mc_hik_set_exposure_auto(void* camera, int enabled);
MC_HIK_API int mc_hik_set_exposure_time(void* camera, float value);
MC_HIK_API int mc_hik_get_exposure_time(void* camera, float* out_value);
MC_HIK_API int mc_hik_set_gain_auto(void* camera, int enabled);
MC_HIK_API int mc_hik_set_gain(void* camera, float value);
MC_HIK_API int mc_hik_get_gain(void* camera, float* out_value);
MC_HIK_API int mc_hik_set_white_balance_auto(void* camera, int enabled);
MC_HIK_API int mc_hik_set_balance_ratio_red(void* camera, int64_t value);
MC_HIK_API int mc_hik_set_balance_ratio_green(void* camera, int64_t value);
MC_HIK_API int mc_hik_set_balance_ratio_blue(void* camera, int64_t value);
MC_HIK_API int mc_hik_start_grabbing(void* camera);
MC_HIK_API int mc_hik_stop_grabbing(void* camera);
MC_HIK_API int mc_hik_get_frame_info(void* camera, uint32_t timeout_ms, mc_hik_frame_info_t* out_frame_info);
MC_HIK_API int mc_hik_get_frame_data(void* camera, uint32_t timeout_ms, uint8_t* buffer, uint32_t capacity, mc_hik_frame_info_t* out_frame_info);
MC_HIK_API int mc_hik_save_features(void* camera, const char* file_path);
MC_HIK_API int mc_hik_load_features(void* camera, const char* file_path);
MC_HIK_API const char* mc_hik_error_to_string(int error_code);

#ifdef __cplusplus
}
#endif
