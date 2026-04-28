#include <iostream>
#include <string>

#include "medical_camera/hikvision/hikvision_camera.h"

using medical_camera::hikvision::HikvisionCameraSdk;

namespace {

void print_status(const char* label, int status) {
    std::cout
        << label
        << ": 0x" << std::hex << status << std::dec
        << " (" << HikvisionCameraSdk::error_to_string(status) << ")\n";
}

void print_divider(const char* title) {
    std::cout << "\n==== " << title << " ====\n";
}

}  // namespace

int main() {
    const auto init_result = HikvisionCameraSdk::initialize();
    if (init_result != MV_OK) {
        std::cerr << "Initialize SDK failed: 0x" << std::hex << init_result << std::dec << '\n';
        return 1;
    }

    auto finalize_guard = []() {
        HikvisionCameraSdk::finalize();
    };

    const auto devices = HikvisionCameraSdk::enumerate_devices(MV_GIGE_DEVICE | MV_USB_DEVICE);
    if (devices.empty()) {
        std::cout << "No Hikvision devices found.\n";
        finalize_guard();
        return 0;
    }

    std::cout << "Detected devices:\n";
    for (const auto& device : devices) {
        std::cout
            << "[" << device.index << "] "
            << device.model_name
            << " SN=" << device.serial_number;
        if (!device.ip_address.empty()) {
            std::cout << " IP=" << device.ip_address;
        }
        std::cout << '\n';
    }

    HikvisionCameraSdk camera;
    const auto open_result = camera.open_by_index(0, MV_GIGE_DEVICE | MV_USB_DEVICE);
    if (open_result != MV_OK) {
        std::cerr << "Open device failed: 0x" << std::hex << open_result << std::dec << '\n';
        finalize_guard();
        return 1;
    }

    float exposure = 0.0f;
    if (camera.get_exposure_time(exposure) == MV_OK) {
        std::cout << "Current exposure: " << exposure << " us\n";
    }

    print_divider("Capability Snapshot");
    const auto snapshot = camera.query_capability_snapshot();
    print_status("Width node", snapshot.width.status);
    if (snapshot.width.available()) {
        std::cout
            << "  width current=" << snapshot.width.value.current
            << " min=" << snapshot.width.value.minimum
            << " max=" << snapshot.width.value.maximum
            << " inc=" << snapshot.width.value.increment << '\n';
    }

    print_status("Exposure node", snapshot.exposure_time.status);
    if (snapshot.exposure_time.available()) {
        std::cout
            << "  exposure current=" << snapshot.exposure_time.value.current
            << " min=" << snapshot.exposure_time.value.minimum
            << " max=" << snapshot.exposure_time.value.maximum << '\n';
    }

    print_status("Gain node", snapshot.gain.status);
    if (snapshot.gain.available()) {
        std::cout
            << "  gain current=" << snapshot.gain.value.current
            << " min=" << snapshot.gain.value.minimum
            << " max=" << snapshot.gain.value.maximum << '\n';
    }

    print_status("Frame rate node", snapshot.frame_rate.status);
    if (snapshot.frame_rate.available()) {
        std::cout
            << "  fps current=" << snapshot.frame_rate.value.current
            << " min=" << snapshot.frame_rate.value.minimum
            << " max=" << snapshot.frame_rate.value.maximum << '\n';
    }

    print_status("PixelFormat node", snapshot.pixel_format.status);
    if (snapshot.pixel_format.available()) {
        std::cout
            << "  pixel format current=" << snapshot.pixel_format.value.current
            << " supported_count=" << snapshot.pixel_format.value.supported_values.size() << '\n';
    }

    print_status("White balance auto node", snapshot.white_balance_auto.status);
    print_status("Balance ratio red node", snapshot.balance_ratio_red.status);
    if (snapshot.balance_ratio_red.available()) {
        std::cout
            << "  red ratio current=" << snapshot.balance_ratio_red.value.current
            << " min=" << snapshot.balance_ratio_red.value.minimum
            << " max=" << snapshot.balance_ratio_red.value.maximum
            << " inc=" << snapshot.balance_ratio_red.value.increment << '\n';
    }

    print_status("Optimal packet size", snapshot.optimal_packet_size_status);
    if (snapshot.optimal_packet_size_status == MV_OK) {
        std::cout << "  optimal packet size=" << snapshot.optimal_packet_size << '\n';
    }

    print_divider("Control Validation");
    if (snapshot.exposure_time.available()) {
        const auto disable_auto_result = camera.set_exposure_auto(false);
        print_status("Disable exposure auto", disable_auto_result);

        const auto original_exposure = snapshot.exposure_time.value.current;
        float target_exposure = original_exposure + 1000.0f;
        if (target_exposure > snapshot.exposure_time.value.maximum) {
            target_exposure = snapshot.exposure_time.value.maximum;
        }
        if (target_exposure < snapshot.exposure_time.value.minimum) {
            target_exposure = snapshot.exposure_time.value.minimum;
        }

        const auto set_exposure_result = camera.set_exposure_time(target_exposure);
        print_status("Set exposure", set_exposure_result);

        float exposure_after_set = 0.0f;
        const auto read_exposure_result = camera.get_exposure_time(exposure_after_set);
        print_status("Read exposure after set", read_exposure_result);
        if (read_exposure_result == MV_OK) {
            std::cout
                << "  exposure before=" << original_exposure
                << " target=" << target_exposure
                << " actual=" << exposure_after_set << '\n';
        }

        const auto restore_exposure_result = camera.set_exposure_time(original_exposure);
        print_status("Restore exposure", restore_exposure_result);
    } else {
        std::cout << "Exposure node unavailable, skip exposure write test.\n";
    }

    print_divider("Grab Validation");
    const auto start_grab_result = camera.start_grabbing();
    print_status("Start grabbing", start_grab_result);
    if (start_grab_result == MV_OK) {
        medical_camera::hikvision::FrameData frame{};
        const auto get_frame_result = camera.get_frame(frame, 1000);
        print_status("Get frame", get_frame_result);
        if (get_frame_result == MV_OK) {
            std::cout
                << "  frame width=" << frame.width
                << " height=" << frame.height
                << " frame_number=" << frame.frame_number
                << " bytes=" << frame.bytes.size()
                << " pixel_type=" << frame.pixel_type << '\n';
        }

        const auto stop_grab_result = camera.stop_grabbing();
        print_status("Stop grabbing", stop_grab_result);
    }

    print_divider("Feature File");
    const auto save_result = camera.save_features("camera_features.mfs");
    if (save_result == MV_OK) {
        std::cout << "Saved feature file: camera_features.mfs\n";
    } else {
        print_status("Save feature file", save_result);
    }

    camera.close();
    finalize_guard();
    return 0;
}
