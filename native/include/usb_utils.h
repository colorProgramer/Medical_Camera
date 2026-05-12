#ifndef MEDICAL_CAMERA_USB_UTILS_H
#define MEDICAL_CAMERA_USB_UTILS_H

#ifdef _WIN32
    #ifdef MEDICAL_CAMERA_USB_EXPORTS
        #define USB_API __declspec(dllexport)
    #else
        #define USB_API __declspec(dllimport)
    #endif
#else
    #define USB_API
#endif

extern "C" {

/**
 * @brief Get the friendly name of a camera by its DirectShow index.
 * 
 * @param index The zero-based index of the camera.
 * @param buffer Buffer to receive the name.
 * @param capacity Capacity of the buffer in wchar_t.
 * @return 0 on success, non-zero error code otherwise.
 */
USB_API int mc_usb_get_device_name(int index, wchar_t* buffer, int capacity);

/**
 * @brief Get the count of video input devices available in the system.
 * 
 * @return Count of devices.
 */
USB_API int mc_usb_get_device_count();

}

#endif // MEDICAL_CAMERA_USB_UTILS_H
