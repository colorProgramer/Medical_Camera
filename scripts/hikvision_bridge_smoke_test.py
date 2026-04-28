from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_camera.bridges.hikvision_bridge import (
    HikvisionBridge,
    MV_DEFAULT_DEVICE_MASK,
)


def main() -> int:
    bridge = HikvisionBridge()
    status = bridge.initialize()
    print("initialize:", hex(status), bridge.error_to_string(status))
    if status != 0:
        return 1

    bridge.create_camera()
    try:
        status, devices = bridge.enumerate_devices(MV_DEFAULT_DEVICE_MASK)
        print("enumerate:", hex(status), bridge.error_to_string(status), devices)
        if status != 0 or not devices:
            return 0

        status = bridge.open_by_index(0, MV_DEFAULT_DEVICE_MASK)
        print("open:", hex(status), bridge.error_to_string(status))
        if status != 0:
            return 1

        status, snapshot = bridge.query_snapshot()
        print("snapshot:", hex(status), bridge.error_to_string(status))
        print("width:", snapshot.width.current, snapshot.width.minimum, snapshot.width.maximum, snapshot.width.increment)
        print("exposure:", snapshot.exposure_time.current, snapshot.exposure_time.minimum, snapshot.exposure_time.maximum)

        status, exposure = bridge.get_exposure_time()
        print("get_exposure:", hex(status), bridge.error_to_string(status), exposure)

        status = bridge.set_exposure_auto(False)
        print("set_exposure_auto:", hex(status), bridge.error_to_string(status))

        status = bridge.start_grabbing()
        print("start_grabbing:", hex(status), bridge.error_to_string(status))
        if status == 0:
            status, frame = bridge.get_frame_info()
            print("get_frame_info:", hex(status), bridge.error_to_string(status), frame.width, frame.height, frame.byte_count)
            capacity = max(snapshot.payload_size.current, frame.byte_count, 1024 * 1024)
            status, frame, data = bridge.get_frame_data(capacity)
            print(
                "get_frame_data:",
                hex(status),
                bridge.error_to_string(status),
                frame.width,
                frame.height,
                frame.byte_count,
                len(data),
            )
            status = bridge.stop_grabbing()
            print("stop_grabbing:", hex(status), bridge.error_to_string(status))

        status = bridge.close()
        print("close:", hex(status), bridge.error_to_string(status))
        return 0
    finally:
        bridge.destroy_camera()
        status = bridge.finalize()
        print("finalize:", hex(status), bridge.error_to_string(status))


if __name__ == "__main__":
    raise SystemExit(main())
