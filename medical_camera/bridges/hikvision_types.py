from __future__ import annotations

from ctypes import Structure, c_char, c_float, c_int, c_int64, c_uint32

MV_GIGE_DEVICE = 0x00000001
MV_USB_DEVICE = 0x00000004
MV_DEFAULT_DEVICE_MASK = MV_GIGE_DEVICE | MV_USB_DEVICE


class McHikDeviceInfo(Structure):
    _fields_ = [
        ("index", c_uint32),
        ("transport_layer_type", c_uint32),
        ("vendor_name", c_char * 64),
        ("model_name", c_char * 64),
        ("serial_number", c_char * 64),
        ("user_defined_name", c_char * 64),
        ("ip_address", c_char * 32),
    ]


class McHikIntNode(Structure):
    _fields_ = [
        ("status", c_int),
        ("current", c_int64),
        ("minimum", c_int64),
        ("maximum", c_int64),
        ("increment", c_int64),
    ]


class McHikFloatNode(Structure):
    _fields_ = [
        ("status", c_int),
        ("current", c_float),
        ("minimum", c_float),
        ("maximum", c_float),
    ]


class McHikEnumNode(Structure):
    _fields_ = [
        ("status", c_int),
        ("current", c_uint32),
        ("supported_count", c_uint32),
        ("supported_values", c_uint32 * 256),
    ]


class McHikBoolNode(Structure):
    _fields_ = [
        ("status", c_int),
        ("current", c_int),
    ]


class McHikStringNode(Structure):
    _fields_ = [
        ("status", c_int),
        ("current", c_char * 256),
    ]


class McHikSnapshot(Structure):
    _fields_ = [
        ("width", McHikIntNode),
        ("height", McHikIntNode),
        ("payload_size", McHikIntNode),
        ("exposure_time", McHikFloatNode),
        ("gain", McHikFloatNode),
        ("frame_rate", McHikFloatNode),
        ("pixel_format", McHikEnumNode),
        ("exposure_auto", McHikEnumNode),
        ("gain_auto", McHikEnumNode),
        ("white_balance_auto", McHikEnumNode),
        ("balance_ratio_selector", McHikEnumNode),
        ("trigger_mode", McHikEnumNode),
        ("trigger_source", McHikEnumNode),
        ("balance_ratio_red", McHikIntNode),
        ("balance_ratio_green", McHikIntNode),
        ("balance_ratio_blue", McHikIntNode),
        ("reverse_x", McHikBoolNode),
        ("reverse_y", McHikBoolNode),
        ("device_user_id", McHikStringNode),
        ("optimal_packet_size_status", c_int),
        ("optimal_packet_size", c_uint32),
    ]


class McHikFrameInfo(Structure):
    _fields_ = [
        ("status", c_int),
        ("width", c_uint32),
        ("height", c_uint32),
        ("frame_number", c_uint32),
        ("pixel_type", c_uint32),
        ("byte_count", c_uint32),
    ]

