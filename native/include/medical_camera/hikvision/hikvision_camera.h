#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "MvCameraControl.h"

namespace medical_camera::hikvision {

struct DeviceDescriptor {
    std::uint32_t index = 0;
    std::uint32_t transport_layer_type = 0;
    std::string vendor_name;
    std::string model_name;
    std::string serial_number;
    std::string user_defined_name;
    std::string ip_address;
};

struct FrameData {
    std::vector<std::uint8_t> bytes;
    std::uint32_t width = 0;
    std::uint32_t height = 0;
    std::uint32_t frame_number = 0;
    std::uint32_t pixel_type = 0;
};

struct IntNodeInfo {
    std::int64_t current = 0;
    std::int64_t minimum = 0;
    std::int64_t maximum = 0;
    std::int64_t increment = 0;
};

struct FloatNodeInfo {
    float current = 0.0f;
    float minimum = 0.0f;
    float maximum = 0.0f;
};

struct EnumNodeInfo {
    std::uint32_t current = 0;
    std::vector<std::uint32_t> supported_values;
};

struct BoolNodeInfo {
    bool current = false;
};

struct StringNodeInfo {
    std::string current;
};

template <typename T>
struct NodeSnapshot {
    int status = static_cast<int>(MV_E_HANDLE);
    T value{};

    bool available() const {
        return status == MV_OK;
    }
};

struct CameraCapabilitySnapshot {
    NodeSnapshot<IntNodeInfo> width;
    NodeSnapshot<IntNodeInfo> height;
    NodeSnapshot<IntNodeInfo> payload_size;

    NodeSnapshot<FloatNodeInfo> exposure_time;
    NodeSnapshot<FloatNodeInfo> gain;
    NodeSnapshot<FloatNodeInfo> frame_rate;

    NodeSnapshot<EnumNodeInfo> pixel_format;
    NodeSnapshot<EnumNodeInfo> exposure_auto;
    NodeSnapshot<EnumNodeInfo> gain_auto;
    NodeSnapshot<EnumNodeInfo> white_balance_auto;
    NodeSnapshot<EnumNodeInfo> balance_ratio_selector;
    NodeSnapshot<EnumNodeInfo> trigger_mode;
    NodeSnapshot<EnumNodeInfo> trigger_source;

    NodeSnapshot<IntNodeInfo> balance_ratio_red;
    NodeSnapshot<IntNodeInfo> balance_ratio_green;
    NodeSnapshot<IntNodeInfo> balance_ratio_blue;

    NodeSnapshot<BoolNodeInfo> reverse_x;
    NodeSnapshot<BoolNodeInfo> reverse_y;
    NodeSnapshot<StringNodeInfo> device_user_id;

    int optimal_packet_size_status = static_cast<int>(MV_E_HANDLE);
    std::uint32_t optimal_packet_size = 0;
};

class HikvisionCameraSdk final {
public:
    HikvisionCameraSdk();
    ~HikvisionCameraSdk();

    HikvisionCameraSdk(const HikvisionCameraSdk&) = delete;
    HikvisionCameraSdk& operator=(const HikvisionCameraSdk&) = delete;

    static int initialize();
    static int finalize();
    static std::vector<DeviceDescriptor> enumerate_devices(std::uint32_t transport_layer_mask);

    int open_by_index(std::uint32_t device_index, std::uint32_t transport_layer_mask);
    int close();

    bool is_open() const;
    bool is_connected() const;

    int start_grabbing();
    int stop_grabbing();
    int get_frame(FrameData& frame, std::uint32_t timeout_ms = 1000);

    int get_width(std::int64_t& value) const;
    int get_width_info(IntNodeInfo& info) const;
    int get_height(std::int64_t& value) const;
    int get_height_info(IntNodeInfo& info) const;
    int set_width(std::int64_t value);
    int set_height(std::int64_t value);

    int get_pixel_format(std::uint32_t& value) const;
    int get_pixel_format_info(EnumNodeInfo& info) const;
    int set_pixel_format(std::uint32_t value);
    int set_pixel_format_by_symbolic(const std::string& value);

    int get_exposure_time(float& value) const;
    int get_exposure_time_info(FloatNodeInfo& info) const;
    int set_exposure_time(float value);
    int set_exposure_auto(bool enabled);
    int get_exposure_auto_info(EnumNodeInfo& info) const;

    int get_gain(float& value) const;
    int get_gain_info(FloatNodeInfo& info) const;
    int set_gain(float value);
    int set_gain_auto(bool enabled);
    int get_gain_auto_info(EnumNodeInfo& info) const;

    int get_frame_rate(float& value) const;
    int get_frame_rate_info(FloatNodeInfo& info) const;
    int set_frame_rate(float value);

    int set_white_balance_auto(bool enabled);
    int get_white_balance_auto_info(EnumNodeInfo& info) const;
    int get_balance_ratio_selector_info(EnumNodeInfo& info) const;
    int get_balance_ratio_red_info(IntNodeInfo& info);
    int get_balance_ratio_green_info(IntNodeInfo& info);
    int get_balance_ratio_blue_info(IntNodeInfo& info);
    int set_balance_ratio_red(std::int64_t value);
    int set_balance_ratio_green(std::int64_t value);
    int set_balance_ratio_blue(std::int64_t value);

    int get_payload_size_info(IntNodeInfo& info) const;
    int get_trigger_mode_info(EnumNodeInfo& info) const;
    int set_trigger_mode_by_symbolic(const std::string& value);
    int get_trigger_source_info(EnumNodeInfo& info) const;
    int set_trigger_source_by_symbolic(const std::string& value);
    int get_reverse_x_info(BoolNodeInfo& info) const;
    int set_reverse_x(bool enabled);
    int get_reverse_y_info(BoolNodeInfo& info) const;
    int set_reverse_y(bool enabled);
    int get_device_user_id_info(StringNodeInfo& info) const;
    int set_device_user_id(const std::string& value);

    int get_optimal_packet_size(std::uint32_t& value) const;
    int set_packet_size(std::int64_t value);

    int save_features(const std::string& file_path);
    int load_features(const std::string& file_path);

    CameraCapabilitySnapshot query_capability_snapshot();
    static const char* error_to_string(int error_code);

private:
    int ensure_handle_created(MV_CC_DEVICE_INFO* device_info);
    int get_int_node(const char* key, IntNodeInfo& info) const;
    int get_float_node(const char* key, FloatNodeInfo& info) const;
    int get_enum_node(const char* key, EnumNodeInfo& info) const;
    int get_bool_node(const char* key, BoolNodeInfo& info) const;
    int get_string_node(const char* key, StringNodeInfo& info) const;
    int set_balance_ratio_selector(const char* selector);
    int get_balance_ratio_info_for_selector(const char* selector, IntNodeInfo& info);
    static std::string to_ip_string(std::uint32_t ip);
    static std::string safe_string(const char* text);

    void* handle_ = nullptr;
};

}  // namespace medical_camera::hikvision
