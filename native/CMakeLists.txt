cmake_minimum_required(VERSION 3.20)

project(medical_camera_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT WIN32)
    message(FATAL_ERROR "medical_camera_native currently supports Windows only.")
endif()

set(MVS_SDK_ROOT "" CACHE PATH "Root directory of Hikrobot MVS SDK")

find_path(MVS_INCLUDE_DIR
    NAMES MvCameraControl.h
    PATHS
        "${MVS_SDK_ROOT}/Development/Includes"
        "${MVS_SDK_ROOT}/Includes"
    NO_DEFAULT_PATH
)

find_library(MVS_CAMERA_CONTROL_LIB
    NAMES MvCameraControl
    PATHS
        "${MVS_SDK_ROOT}/Development/Libraries/win64"
        "${MVS_SDK_ROOT}/Libraries/win64"
        "${MVS_SDK_ROOT}/lib/win64"
    NO_DEFAULT_PATH
)

if(MVS_INCLUDE_DIR AND MVS_CAMERA_CONTROL_LIB)
    message(STATUS "Hikvision MVS SDK found. Building Hikvision targets.")
    set(HIK_FOUND TRUE)
else()
    message(WARNING "Hikvision MVS SDK not found. Skipping Hikvision targets. (Set MVS_SDK_ROOT if needed)")
    set(HIK_FOUND FALSE)
endif()

if(HIK_FOUND)
    add_library(medical_camera_hikvision STATIC
        src/hikvision_camera.cpp
    )

    target_include_directories(medical_camera_hikvision
        PUBLIC
            ${CMAKE_CURRENT_SOURCE_DIR}/include
            ${MVS_INCLUDE_DIR}
    )

    target_link_libraries(medical_camera_hikvision
        PUBLIC
            ${MVS_CAMERA_CONTROL_LIB}
    )

    target_compile_definitions(medical_camera_hikvision
        PRIVATE
            NOMINMAX
            WIN32_LEAN_AND_MEAN
    )

    add_library(medical_camera_hikvision_capi SHARED
        src/hikvision_c_api.cpp
    )

    target_include_directories(medical_camera_hikvision_capi
        PUBLIC
            ${CMAKE_CURRENT_SOURCE_DIR}/include
            ${MVS_INCLUDE_DIR}
    )

    target_link_libraries(medical_camera_hikvision_capi
        PRIVATE
            medical_camera_hikvision
    )

    target_compile_definitions(medical_camera_hikvision_capi
        PRIVATE
            MEDICAL_CAMERA_HIKVISION_CAPI_EXPORTS
            NOMINMAX
            WIN32_LEAN_AND_MEAN
    )

    add_executable(hikvision_sdk_demo
        examples/hikvision_sdk_demo.cpp
    )

    target_link_libraries(hikvision_sdk_demo
        PRIVATE
            medical_camera_hikvision
    )
endif()

# USB Utilities (DirectShow based)
add_library(medical_camera_usb SHARED
    src/usb_utils.cpp
)

target_include_directories(medical_camera_usb
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_definitions(medical_camera_usb
    PRIVATE
        MEDICAL_CAMERA_USB_EXPORTS
        NOMINMAX
        WIN32_LEAN_AND_MEAN
)
