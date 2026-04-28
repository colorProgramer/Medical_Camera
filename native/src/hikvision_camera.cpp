#include "medical_camera/hikvision/hikvision_camera.h"

#include <cstring>
#include <sstream>
#include <stdexcept>

namespace medical_camera::hikvision {

namespace {

constexpr std::uint32_t kDefaultTransportMask = MV_GIGE_DEVICE | MV_USB_DEVICE;

}  // namespace

HikvisionCameraSdk::HikvisionCameraSdk() = default;

HikvisionCameraSdk::~HikvisionCameraSdk() {
    close();
}

int HikvisionCameraSdk::initialize() {
    return MV_CC_Initialize();
}

int HikvisionCameraSdk::finalize() {
    return MV_CC_Finalize();
}

std::vector<DeviceDescriptor> HikvisionCameraSdk::enumerate_devices(std::uint32_t transport_layer_mask) {
    MV_CC_DEVICE_INFO_LIST device_list{};
    const auto result = MV_CC_EnumDevices(transport_layer_mask == 0 ? kDefaultTransportMask : transport_layer_mask, &device_list);
    if (result != MV_OK) {
        return {};
    }

    std::vector<DeviceDescriptor> devices;
    devices.reserve(device_list.nDeviceNum);

    for (std::uint32_t index = 0; index < device_list.nDeviceNum; ++index) {
        auto* device_info = device_list.pDeviceInfo[index];
        if (device_info == nullptr) {
            continue;
        }

        DeviceDescriptor descriptor{};
        descriptor.index = index;
        descriptor.transport_layer_type = device_info->nTLayerType;

        if (device_info->nTLayerType == MV_GIGE_DEVICE) {
            descriptor.vendor_name = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stGigEInfo.chManufacturerName));
            descriptor.model_name = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stGigEInfo.chModelName));
            descriptor.serial_number = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stGigEInfo.chSerialNumber));
            descriptor.user_defined_name = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stGigEInfo.chUserDefinedName));
            descriptor.ip_address = to_ip_string(device_info->SpecialInfo.stGigEInfo.nCurrentIp);
        } else if (device_info->nTLayerType == MV_USB_DEVICE) {
            descriptor.vendor_name = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stUsb3VInfo.chManufacturerName));
            descriptor.model_name = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stUsb3VInfo.chModelName));
            descriptor.serial_number = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stUsb3VInfo.chSerialNumber));
            descriptor.user_defined_name = safe_string(reinterpret_cast<const char*>(device_info->SpecialInfo.stUsb3VInfo.chUserDefinedName));
        }

        devices.push_back(std::move(descriptor));
    }

    return devices;
}

int HikvisionCameraSdk::open_by_index(std::uint32_t device_index, std::uint32_t transport_layer_mask) {
    MV_CC_DEVICE_INFO_LIST device_list{};
    const auto enumerate_result = MV_CC_EnumDevices(
        transport_layer_mask == 0 ? kDefaultTransportMask : transport_layer_mask,
        &device_list
    );
    if (enumerate_result != MV_OK) {
        return enumerate_result;
    }

    if (device_index >= device_list.nDeviceNum) {
        return MV_E_PARAMETER;
    }

    return ensure_handle_created(device_list.pDeviceInfo[device_index]);
}

int HikvisionCameraSdk::close() {
    if (handle_ == nullptr) {
        return MV_OK;
    }

    MV_CC_CloseDevice(handle_);
    const auto result = MV_CC_DestroyHandle(handle_);
    handle_ = nullptr;
    return result;
}

bool HikvisionCameraSdk::is_open() const {
    return handle_ != nullptr;
}

bool HikvisionCameraSdk::is_connected() const {
    return handle_ != nullptr && MV_CC_IsDeviceConnected(handle_);
}

int HikvisionCameraSdk::start_grabbing() {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_StartGrabbing(handle_);
}

int HikvisionCameraSdk::stop_grabbing() {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_StopGrabbing(handle_);
}

int HikvisionCameraSdk::get_frame(FrameData& frame, std::uint32_t timeout_ms) {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }

    MV_FRAME_OUT frame_out{};
    const auto result = MV_CC_GetImageBuffer(handle_, &frame_out, timeout_ms);
    if (result != MV_OK) {
        return result;
    }

    frame.width = frame_out.stFrameInfo.nWidth;
    frame.height = frame_out.stFrameInfo.nHeight;
    frame.frame_number = frame_out.stFrameInfo.nFrameNum;
    frame.pixel_type = frame_out.stFrameInfo.enPixelType;
    frame.bytes.resize(frame_out.stFrameInfo.nFrameLen);
    std::memcpy(frame.bytes.data(), frame_out.pBufAddr, frame_out.stFrameInfo.nFrameLen);

    MV_CC_FreeImageBuffer(handle_, &frame_out);
    return MV_OK;
}

int HikvisionCameraSdk::get_width(std::int64_t& value) const {
    IntNodeInfo info{};
    const auto result = get_width_info(info);
    if (result == MV_OK) {
        value = info.current;
    }
    return result;
}

int HikvisionCameraSdk::get_width_info(IntNodeInfo& info) const {
    return get_int_node("Width", info);
}

int HikvisionCameraSdk::get_height(std::int64_t& value) const {
    IntNodeInfo info{};
    const auto result = get_height_info(info);
    if (result == MV_OK) {
        value = info.current;
    }
    return result;
}

int HikvisionCameraSdk::get_height_info(IntNodeInfo& info) const {
    return get_int_node("Height", info);
}

int HikvisionCameraSdk::set_width(std::int64_t value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetIntValueEx(handle_, "Width", value);
}

int HikvisionCameraSdk::set_height(std::int64_t value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetIntValueEx(handle_, "Height", value);
}

int HikvisionCameraSdk::get_pixel_format(std::uint32_t& value) const {
    EnumNodeInfo info{};
    const auto result = get_pixel_format_info(info);
    if (result == MV_OK) {
        value = info.current;
    }
    return result;
}

int HikvisionCameraSdk::get_pixel_format_info(EnumNodeInfo& info) const {
    return get_enum_node("PixelFormat", info);
}

int HikvisionCameraSdk::set_pixel_format(std::uint32_t value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValue(handle_, "PixelFormat", value);
}

int HikvisionCameraSdk::set_pixel_format_by_symbolic(const std::string& value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValueByString(handle_, "PixelFormat", value.c_str());
}

int HikvisionCameraSdk::get_exposure_time(float& value) const {
    FloatNodeInfo info{};
    const auto result = get_exposure_time_info(info);
    if (result == MV_OK) {
        value = info.current;
    }
    return result;
}

int HikvisionCameraSdk::get_exposure_time_info(FloatNodeInfo& info) const {
    return get_float_node("ExposureTime", info);
}

int HikvisionCameraSdk::set_exposure_time(float value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetFloatValue(handle_, "ExposureTime", value);
}

int HikvisionCameraSdk::set_exposure_auto(bool enabled) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValueByString(
        handle_,
        "ExposureAuto",
        enabled ? "Continuous" : "Off"
    );
}

int HikvisionCameraSdk::get_exposure_auto_info(EnumNodeInfo& info) const {
    return get_enum_node("ExposureAuto", info);
}

int HikvisionCameraSdk::get_gain(float& value) const {
    FloatNodeInfo info{};
    const auto result = get_gain_info(info);
    if (result == MV_OK) {
        value = info.current;
    }
    return result;
}

int HikvisionCameraSdk::get_gain_info(FloatNodeInfo& info) const {
    return get_float_node("Gain", info);
}

int HikvisionCameraSdk::set_gain(float value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetFloatValue(handle_, "Gain", value);
}

int HikvisionCameraSdk::set_gain_auto(bool enabled) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValueByString(
        handle_,
        "GainAuto",
        enabled ? "Continuous" : "Off"
    );
}

int HikvisionCameraSdk::get_gain_auto_info(EnumNodeInfo& info) const {
    return get_enum_node("GainAuto", info);
}

int HikvisionCameraSdk::get_frame_rate(float& value) const {
    FloatNodeInfo info{};
    const auto result = get_frame_rate_info(info);
    if (result == MV_OK) {
        value = info.current;
    }
    return result;
}

int HikvisionCameraSdk::get_frame_rate_info(FloatNodeInfo& info) const {
    auto result = get_float_node("AcquisitionFrameRate", info);
    if (result != MV_OK) {
        result = get_float_node("ResultingFrameRate", info);
    }
    return result;
}

int HikvisionCameraSdk::set_frame_rate(float value) {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }

    auto result = MV_CC_SetBoolValue(handle_, "AcquisitionFrameRateEnable", true);
    if (result != MV_OK) {
        return result;
    }

    return MV_CC_SetFloatValue(handle_, "AcquisitionFrameRate", value);
}

int HikvisionCameraSdk::set_white_balance_auto(bool enabled) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValueByString(
        handle_,
        "BalanceWhiteAuto",
        enabled ? "Continuous" : "Off"
    );
}

int HikvisionCameraSdk::get_white_balance_auto_info(EnumNodeInfo& info) const {
    return get_enum_node("BalanceWhiteAuto", info);
}

int HikvisionCameraSdk::get_balance_ratio_selector_info(EnumNodeInfo& info) const {
    return get_enum_node("BalanceRatioSelector", info);
}

int HikvisionCameraSdk::get_balance_ratio_red_info(IntNodeInfo& info) {
    return get_balance_ratio_info_for_selector("Red", info);
}

int HikvisionCameraSdk::get_balance_ratio_green_info(IntNodeInfo& info) {
    return get_balance_ratio_info_for_selector("Green", info);
}

int HikvisionCameraSdk::get_balance_ratio_blue_info(IntNodeInfo& info) {
    return get_balance_ratio_info_for_selector("Blue", info);
}

int HikvisionCameraSdk::set_balance_ratio_red(std::int64_t value) {
    auto result = set_balance_ratio_selector("Red");
    if (result != MV_OK) {
        return result;
    }
    return MV_CC_SetIntValueEx(handle_, "BalanceRatio", value);
}

int HikvisionCameraSdk::set_balance_ratio_green(std::int64_t value) {
    auto result = set_balance_ratio_selector("Green");
    if (result != MV_OK) {
        return result;
    }
    return MV_CC_SetIntValueEx(handle_, "BalanceRatio", value);
}

int HikvisionCameraSdk::set_balance_ratio_blue(std::int64_t value) {
    auto result = set_balance_ratio_selector("Blue");
    if (result != MV_OK) {
        return result;
    }
    return MV_CC_SetIntValueEx(handle_, "BalanceRatio", value);
}

int HikvisionCameraSdk::get_payload_size_info(IntNodeInfo& info) const {
    return get_int_node("PayloadSize", info);
}

int HikvisionCameraSdk::get_trigger_mode_info(EnumNodeInfo& info) const {
    return get_enum_node("TriggerMode", info);
}

int HikvisionCameraSdk::set_trigger_mode_by_symbolic(const std::string& value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValueByString(handle_, "TriggerMode", value.c_str());
}

int HikvisionCameraSdk::get_trigger_source_info(EnumNodeInfo& info) const {
    return get_enum_node("TriggerSource", info);
}

int HikvisionCameraSdk::set_trigger_source_by_symbolic(const std::string& value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetEnumValueByString(handle_, "TriggerSource", value.c_str());
}

int HikvisionCameraSdk::get_reverse_x_info(BoolNodeInfo& info) const {
    return get_bool_node("ReverseX", info);
}

int HikvisionCameraSdk::set_reverse_x(bool enabled) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetBoolValue(handle_, "ReverseX", enabled);
}

int HikvisionCameraSdk::get_reverse_y_info(BoolNodeInfo& info) const {
    return get_bool_node("ReverseY", info);
}

int HikvisionCameraSdk::set_reverse_y(bool enabled) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetBoolValue(handle_, "ReverseY", enabled);
}

int HikvisionCameraSdk::get_device_user_id_info(StringNodeInfo& info) const {
    return get_string_node("DeviceUserID", info);
}

int HikvisionCameraSdk::set_device_user_id(const std::string& value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetStringValue(handle_, "DeviceUserID", value.c_str());
}

int HikvisionCameraSdk::get_optimal_packet_size(std::uint32_t& value) const {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    const auto packet_size = MV_CC_GetOptimalPacketSize(handle_);
    if (packet_size <= 0) {
        return packet_size;
    }
    value = static_cast<std::uint32_t>(packet_size);
    return MV_OK;
}

int HikvisionCameraSdk::set_packet_size(std::int64_t value) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_SetIntValueEx(handle_, "GevSCPSPacketSize", value);
}

int HikvisionCameraSdk::save_features(const std::string& file_path) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_FeatureSave(handle_, file_path.c_str());
}

int HikvisionCameraSdk::load_features(const std::string& file_path) {
    return handle_ == nullptr ? MV_E_HANDLE : MV_CC_FeatureLoad(handle_, file_path.c_str());
}

CameraCapabilitySnapshot HikvisionCameraSdk::query_capability_snapshot() {
    CameraCapabilitySnapshot snapshot{};

    snapshot.width.status = get_width_info(snapshot.width.value);
    snapshot.height.status = get_height_info(snapshot.height.value);
    snapshot.payload_size.status = get_payload_size_info(snapshot.payload_size.value);

    snapshot.exposure_time.status = get_exposure_time_info(snapshot.exposure_time.value);
    snapshot.gain.status = get_gain_info(snapshot.gain.value);
    snapshot.frame_rate.status = get_frame_rate_info(snapshot.frame_rate.value);

    snapshot.pixel_format.status = get_pixel_format_info(snapshot.pixel_format.value);
    snapshot.exposure_auto.status = get_exposure_auto_info(snapshot.exposure_auto.value);
    snapshot.gain_auto.status = get_gain_auto_info(snapshot.gain_auto.value);
    snapshot.white_balance_auto.status = get_white_balance_auto_info(snapshot.white_balance_auto.value);
    snapshot.balance_ratio_selector.status = get_balance_ratio_selector_info(snapshot.balance_ratio_selector.value);
    snapshot.trigger_mode.status = get_trigger_mode_info(snapshot.trigger_mode.value);
    snapshot.trigger_source.status = get_trigger_source_info(snapshot.trigger_source.value);

    snapshot.balance_ratio_red.status = get_balance_ratio_red_info(snapshot.balance_ratio_red.value);
    snapshot.balance_ratio_green.status = get_balance_ratio_green_info(snapshot.balance_ratio_green.value);
    snapshot.balance_ratio_blue.status = get_balance_ratio_blue_info(snapshot.balance_ratio_blue.value);

    snapshot.reverse_x.status = get_reverse_x_info(snapshot.reverse_x.value);
    snapshot.reverse_y.status = get_reverse_y_info(snapshot.reverse_y.value);
    snapshot.device_user_id.status = get_device_user_id_info(snapshot.device_user_id.value);

    snapshot.optimal_packet_size_status = get_optimal_packet_size(snapshot.optimal_packet_size);
    return snapshot;
}

const char* HikvisionCameraSdk::error_to_string(int error_code) {
    switch (error_code) {
    case MV_OK: return "success";
    case MV_E_HANDLE: return "invalid handle";
    case MV_E_SUPPORT: return "not supported";
    case MV_E_BUFOVER: return "buffer overflow";
    case MV_E_CALLORDER: return "invalid call order";
    case MV_E_PARAMETER: return "invalid parameter";
    case MV_E_RESOURCE: return "resource allocation failed";
    case MV_E_NODATA: return "no data";
    case MV_E_PRECONDITION: return "precondition error";
    case MV_E_VERSION: return "version mismatch";
    case MV_E_NOENOUGH_BUF: return "insufficient buffer";
    case MV_E_ABNORMAL_IMAGE: return "abnormal image";
    case MV_E_LOAD_LIBRARY: return "failed to load library";
    case MV_E_NOOUTBUF: return "no output buffer";
    case MV_E_ENCRYPT: return "encryption error";
    case MV_E_OPENFILE: return "open file error";
    case MV_E_BUF_IN_USE: return "buffer already in use";
    case MV_E_BUF_INVALID: return "buffer invalid";
    case MV_E_NOALIGN_BUF: return "buffer alignment error";
    case MV_E_NOENOUGH_BUF_NUM: return "insufficient buffer count";
    case MV_E_PORT_IN_USE: return "port in use";
    case MV_E_IMAGE_DECODEC: return "image decode error";
    case MV_E_UINT32_LIMIT: return "image too large for uint32 API";
    case MV_E_IMAGE_HEIGHT: return "abnormal image height";
    case MV_E_NOENOUGH_DDR: return "insufficient DDR cache";
    case MV_E_NOENOUGH_STREAM: return "insufficient stream channel";
    case MV_E_NORESPONSE: return "device no response";
    case MV_E_GC_GENERIC: return "GenICam generic error";
    case MV_E_GC_ARGUMENT: return "GenICam invalid argument";
    case MV_E_GC_RANGE: return "GenICam value out of range";
    case MV_E_GC_PROPERTY: return "GenICam property error";
    case MV_E_GC_RUNTIME: return "GenICam runtime error";
    case MV_E_GC_LOGICAL: return "GenICam logical error";
    case MV_E_GC_ACCESS: return "GenICam access error";
    case MV_E_GC_TIMEOUT: return "GenICam timeout";
    case MV_E_NOT_IMPLEMENTED: return "command not implemented";
    case MV_E_INVALID_ADDRESS: return "invalid address";
    case MV_E_WRITE_PROTECT: return "write protected";
    case MV_E_ACCESS_DENIED: return "access denied";
    case MV_E_BUSY: return "device busy";
    case MV_E_PACKET: return "packet error";
    case MV_E_NETER: return "network error";
    case MV_E_IP_CONFLICT: return "ip conflict";
    case MV_E_USB_READ: return "usb read error";
    case MV_E_USB_WRITE: return "usb write error";
    case MV_E_USB_DEVICE: return "usb device error";
    case MV_E_USB_GENICAM: return "usb genicam error";
    case MV_E_USB_BANDWIDTH: return "usb bandwidth insufficient";
    case MV_E_USB_DRIVER: return "usb driver mismatch";
    default: return "unknown error";
    }
}

int HikvisionCameraSdk::ensure_handle_created(MV_CC_DEVICE_INFO* device_info) {
    if (device_info == nullptr) {
        return MV_E_PARAMETER;
    }

    if (handle_ != nullptr) {
        return MV_E_CALLORDER;
    }

    auto result = MV_CC_CreateHandle(&handle_, device_info);
    if (result != MV_OK) {
        return result;
    }

    result = MV_CC_OpenDevice(handle_);
    if (result != MV_OK) {
        MV_CC_DestroyHandle(handle_);
        handle_ = nullptr;
    }
    return result;
}

int HikvisionCameraSdk::get_int_node(const char* key, IntNodeInfo& info) const {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    MVCC_INTVALUE_EX int_value{};
    const auto result = MV_CC_GetIntValueEx(handle_, key, &int_value);
    if (result == MV_OK) {
        info.current = int_value.nCurValue;
        info.minimum = int_value.nMin;
        info.maximum = int_value.nMax;
        info.increment = int_value.nInc;
    }
    return result;
}

int HikvisionCameraSdk::get_float_node(const char* key, FloatNodeInfo& info) const {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    MVCC_FLOATVALUE float_value{};
    const auto result = MV_CC_GetFloatValue(handle_, key, &float_value);
    if (result == MV_OK) {
        info.current = float_value.fCurValue;
        info.minimum = float_value.fMin;
        info.maximum = float_value.fMax;
    }
    return result;
}

int HikvisionCameraSdk::get_enum_node(const char* key, EnumNodeInfo& info) const {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    MVCC_ENUMVALUE_EX enum_value{};
    const auto result = MV_CC_GetEnumValueEx(handle_, key, &enum_value);
    if (result == MV_OK) {
        info.current = enum_value.nCurValue;
        info.supported_values.assign(enum_value.nSupportValue, enum_value.nSupportValue + enum_value.nSupportedNum);
    }
    return result;
}

int HikvisionCameraSdk::get_bool_node(const char* key, BoolNodeInfo& info) const {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    bool current = false;
    const auto result = MV_CC_GetBoolValue(handle_, key, &current);
    if (result == MV_OK) {
        info.current = current;
    }
    return result;
}

int HikvisionCameraSdk::get_string_node(const char* key, StringNodeInfo& info) const {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    MVCC_STRINGVALUE string_value{};
    const auto result = MV_CC_GetStringValue(handle_, key, &string_value);
    if (result == MV_OK) {
        info.current = safe_string(string_value.chCurValue);
    }
    return result;
}

int HikvisionCameraSdk::set_balance_ratio_selector(const char* selector) {
    if (handle_ == nullptr) {
        return MV_E_HANDLE;
    }
    return MV_CC_SetEnumValueByString(handle_, "BalanceRatioSelector", selector);
}

int HikvisionCameraSdk::get_balance_ratio_info_for_selector(const char* selector, IntNodeInfo& info) {
    const auto result = set_balance_ratio_selector(selector);
    if (result != MV_OK) {
        return result;
    }
    return get_int_node("BalanceRatio", info);
}

std::string HikvisionCameraSdk::to_ip_string(std::uint32_t ip) {
    std::ostringstream stream;
    stream
        << ((ip & 0xff000000) >> 24) << '.'
        << ((ip & 0x00ff0000) >> 16) << '.'
        << ((ip & 0x0000ff00) >> 8) << '.'
        << (ip & 0x000000ff);
    return stream.str();
}

std::string HikvisionCameraSdk::safe_string(const char* text) {
    return text == nullptr ? std::string{} : std::string(text);
}

}  // namespace medical_camera::hikvision
