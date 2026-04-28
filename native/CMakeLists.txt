cmake_minimum_required(VERSION 3.20)

project(medical_camera_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT WIN32)
    message(FATAL_ERROR "medical_camera_native currently supports Windows only.")
endif()

set(MVS_SDK_ROOT "" CACHE PATH "Root directory of Hikrobot MVS SDK")

if(NOT MVS_SDK_ROOT)
    message(FATAL_ERROR "Please set MVS_SDK_ROOT to your Hikrobot MVS SDK installation path.")
endif()

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

if(NOT MVS_INCLUDE_DIR)
    message(FATAL_ERROR "MvCameraControl.h not found under MVS_SDK_ROOT.")
endif()

if(NOT MVS_CAMERA_CONTROL_LIB)
    message(FATAL_ERROR "MvCameraControl.lib not found under MVS_SDK_ROOT.")
endif()

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
