from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceCapabilities:
    supports_exposure: bool = False
    supports_gain: bool = False
    supports_white_balance: bool = False
    supports_auto_controls: bool = False
    supports_mfs: bool = False
    supports_resolution: bool = True
    supports_pixel_format: bool = True
    supports_fps: bool = True


@dataclass(frozen=True)
class DeviceProfile:
    key: str
    title: str
    sample_device: str
    capabilities: DeviceCapabilities


HIKVISION_PROFILE = DeviceProfile(
    key="hikvision",
    title="海康工业相机",
    sample_device="MV-CA013-20GM (SN: FJ01234567)",
    capabilities=DeviceCapabilities(
        supports_exposure=True,
        supports_gain=True,
        supports_white_balance=True,
        supports_auto_controls=True,
        supports_mfs=True,
    ),
)


USB_PROFILE = DeviceProfile(
    key="usb",
    title="USB相机",
    sample_device="USB Camera HD Pro",
    capabilities=DeviceCapabilities(
        supports_exposure=False,
        supports_gain=False,
        supports_white_balance=False,
        supports_auto_controls=False,
        supports_mfs=False,
    ),
)


DEVICE_PROFILES = {
    HIKVISION_PROFILE.key: HIKVISION_PROFILE,
    USB_PROFILE.key: USB_PROFILE,
}
