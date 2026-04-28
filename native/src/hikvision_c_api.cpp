#include "medical_camera/hikvision/hikvision_c_api.h"

#include <algorithm>
#include <cstring>

#include "medical_camera/hikvision/hikvision_camera.h"

using medical_camera::hikvision::BoolNodeInfo;
using medical_camera::hikvision::CameraCapabilitySnapshot;
using medical_camera::hikvision::DeviceDescriptor;
using medical_camera::hikvision::EnumNodeInfo;
using medical_camera::hikvision::FloatNodeInfo;
using medical_camera::hikvision::FrameData;
using medical_camera::hikvision::HikvisionCameraSdk;
using medical_camera::hikvision::IntNodeInfo;
using medical_camera::hikvision::StringNodeInfo;

namespace {

template <typename CharArray>
void copy_string(const std::string& source, CharArray& target) {
    std::memset(target, 0, sizeof(target));
    const auto count = std::min(source.size(), sizeof(target) - 1);
    std::memcpy(target, source.data(), count);
}

void copy_device(const DeviceDescriptor& source, mc_hik_device_info_t& target) {
    target.index = source.index;
    target.transport_layer_type = source.transport_layer_type;
    copy_string(source.vendor_name, target.vendor_name);
    copy_string(source.model_name, target.model_name);
    copy_string(source.serial_number, target.serial_number);
    copy_string(source.user_defined_name, target.user_defined_name);
    copy_string(source.ip_address, target.ip_address);
}

void copy_int_node(const medical_camera::hikvision::NodeSnapshot<IntNodeInfo>& source, mc_hik_int_node_t& target) {
    target.status = source.status;
    target.current = source.value.current;
    target.minimum = source.value.minimum;
    target.maximum = source.value.maximum;
    target.increment = source.value.increment;
}

void copy_float_node(const medical_camera::hikvision::NodeSnapshot<FloatNodeInfo>& source, mc_hik_float_node_t& target) {
    target.status = source.status;
    target.current = source.value.current;
    target.minimum = source.value.minimum;
    target.maximum = source.value.maximum;
}

void copy_enum_node(const medical_camera::hikvision::NodeSnapshot<EnumNodeInfo>& source, mc_hik_enum_node_t& target) {
    target.status = source.status;
    target.current = source.value.current;
    target.supported_count = static_cast<uint32_t>(std::min<size_t>(source.value.supported_values.size(), 256));
    std::memset(target.supported_values, 0, sizeof(target.supported_values));
    for (uint32_t index = 0; index < target.supported_count; ++index) {
        target.supported_values[index] = source.value.supported_values[index];
    }
}

void copy_bool_node(const medical_camera::hikvision::NodeSnapshot<BoolNodeInfo>& source, mc_hik_bool_node_t& target) {
    target.status = source.status;
    target.current = source.value.current ? 1 : 0;
}

void copy_string_node(const medical_camera::hikvision::NodeSnapshot<StringNodeInfo>& source, mc_hik_string_node_t& target) {
    target.status = source.status;
    copy_string(source.value.current, target.current);
}

void copy_snapshot(const CameraCapabilitySnapshot& source, mc_hik_snapshot_t& target) {
    copy_int_node(source.width, target.width);
    copy_int_node(source.height, target.height);
    copy_int_node(source.payload_size, target.payload_size);

    copy_float_node(source.exposure_time, target.exposure_time);
    copy_float_node(source.gain, target.gain);
    copy_float_node(source.frame_rate, target.frame_rate);

    copy_enum_node(source.pixel_format, target.pixel_format);
    copy_enum_node(source.exposure_auto, target.exposure_auto);
    copy_enum_node(source.gain_auto, target.gain_auto);
    copy_enum_node(source.white_balance_auto, target.white_balance_auto);
    copy_enum_node(source.balance_ratio_selector, target.balance_ratio_selector);
    copy_enum_node(source.trigger_mode, target.trigger_mode);
    copy_enum_node(source.trigger_source, target.trigger_source);

    copy_int_node(source.balance_ratio_red, target.balance_ratio_red);
    copy_int_node(source.balance_ratio_green, target.balance_ratio_green);
    copy_int_node(source.balance_ratio_blue, target.balance_ratio_blue);

    copy_bool_node(source.reverse_x, target.reverse_x);
    copy_bool_node(source.reverse_y, target.reverse_y);
    copy_string_node(source.device_user_id, target.device_user_id);

    target.optimal_packet_size_status = source.optimal_packet_size_status;
    target.optimal_packet_size = source.optimal_packet_size;
}

HikvisionCameraSdk* as_camera(void* camera) {
    return static_cast<HikvisionCameraSdk*>(camera);
}

}  // namespace

int mc_hik_initialize(void) {
    return HikvisionCameraSdk::initialize();
}

int mc_hik_finalize(void) {
    return HikvisionCameraSdk::finalize();
}

int mc_hik_enumerate_devices(uint32_t transport_layer_mask, mc_hik_device_info_t* devices, uint32_t capacity, uint32_t* out_count) {
    if (out_count == nullptr) {
        return MV_E_PARAMETER;
    }

    const auto device_list = HikvisionCameraSdk::enumerate_devices(transport_layer_mask);
    *out_count = static_cast<uint32_t>(device_list.size());

    if (devices == nullptr || capacity == 0) {
        return MV_OK;
    }

    const auto count = std::min<uint32_t>(capacity, *out_count);
    for (uint32_t index = 0; index < count; ++index) {
        copy_device(device_list[index], devices[index]);
    }
    return MV_OK;
}

void* mc_hik_create_camera(void) {
    return new HikvisionCameraSdk();
}

void mc_hik_destroy_camera(void* camera) {
    delete as_camera(camera);
}

int mc_hik_open_by_index(void* camera, uint32_t device_index, uint32_t transport_layer_mask) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->open_by_index(device_index, transport_layer_mask);
}

int mc_hik_close(void* camera) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->close();
}

int mc_hik_is_connected(void* camera) {
    return camera == nullptr ? 0 : (as_camera(camera)->is_connected() ? 1 : 0);
}

int mc_hik_query_snapshot(void* camera, mc_hik_snapshot_t* snapshot) {
    if (camera == nullptr || snapshot == nullptr) {
        return MV_E_PARAMETER;
    }
    const auto native_snapshot = as_camera(camera)->query_capability_snapshot();
    copy_snapshot(native_snapshot, *snapshot);
    return MV_OK;
}

int mc_hik_set_exposure_auto(void* camera, int enabled) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_exposure_auto(enabled != 0);
}

int mc_hik_set_exposure_time(void* camera, float value) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_exposure_time(value);
}

int mc_hik_get_exposure_time(void* camera, float* out_value) {
    if (camera == nullptr || out_value == nullptr) {
        return MV_E_PARAMETER;
    }
    return as_camera(camera)->get_exposure_time(*out_value);
}

int mc_hik_set_gain_auto(void* camera, int enabled) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_gain_auto(enabled != 0);
}

int mc_hik_set_gain(void* camera, float value) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_gain(value);
}

int mc_hik_get_gain(void* camera, float* out_value) {
    if (camera == nullptr || out_value == nullptr) {
        return MV_E_PARAMETER;
    }
    return as_camera(camera)->get_gain(*out_value);
}

int mc_hik_set_white_balance_auto(void* camera, int enabled) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_white_balance_auto(enabled != 0);
}

int mc_hik_set_balance_ratio_red(void* camera, int64_t value) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_balance_ratio_red(value);
}

int mc_hik_set_balance_ratio_green(void* camera, int64_t value) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_balance_ratio_green(value);
}

int mc_hik_set_balance_ratio_blue(void* camera, int64_t value) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->set_balance_ratio_blue(value);
}

int mc_hik_start_grabbing(void* camera) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->start_grabbing();
}

int mc_hik_stop_grabbing(void* camera) {
    return camera == nullptr ? MV_E_HANDLE : as_camera(camera)->stop_grabbing();
}

int mc_hik_get_frame_info(void* camera, uint32_t timeout_ms, mc_hik_frame_info_t* out_frame_info) {
    if (camera == nullptr || out_frame_info == nullptr) {
        return MV_E_PARAMETER;
    }

    FrameData frame{};
    const auto result = as_camera(camera)->get_frame(frame, timeout_ms);
    out_frame_info->status = result;
    out_frame_info->width = frame.width;
    out_frame_info->height = frame.height;
    out_frame_info->frame_number = frame.frame_number;
    out_frame_info->pixel_type = frame.pixel_type;
    out_frame_info->byte_count = static_cast<uint32_t>(frame.bytes.size());
    return result;
}

int mc_hik_get_frame_data(void* camera, uint32_t timeout_ms, uint8_t* buffer, uint32_t capacity, mc_hik_frame_info_t* out_frame_info) {
    if (camera == nullptr || buffer == nullptr || out_frame_info == nullptr) {
        return MV_E_PARAMETER;
    }

    FrameData frame{};
    const auto result = as_camera(camera)->get_frame(frame, timeout_ms);
    out_frame_info->status = result;
    out_frame_info->width = frame.width;
    out_frame_info->height = frame.height;
    out_frame_info->frame_number = frame.frame_number;
    out_frame_info->pixel_type = frame.pixel_type;
    out_frame_info->byte_count = static_cast<uint32_t>(frame.bytes.size());
    if (result != MV_OK) {
        return result;
    }

    if (capacity < frame.bytes.size()) {
        return MV_E_NOENOUGH_BUF;
    }

    std::memcpy(buffer, frame.bytes.data(), frame.bytes.size());
    return MV_OK;
}

int mc_hik_save_features(void* camera, const char* file_path) {
    if (camera == nullptr || file_path == nullptr) {
        return MV_E_PARAMETER;
    }
    return as_camera(camera)->save_features(file_path);
}

int mc_hik_load_features(void* camera, const char* file_path) {
    if (camera == nullptr || file_path == nullptr) {
        return MV_E_PARAMETER;
    }
    return as_camera(camera)->load_features(file_path);
}

const char* mc_hik_error_to_string(int error_code) {
    return HikvisionCameraSdk::error_to_string(error_code);
}
