import win32com.client

def get_possible_camera_names():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        cameras = []
        for device in wmi.InstancesOf("Win32_PnPEntity"):
            name = str(device.Caption)
            pnp_class = str(device.PNPClass)
            if (pnp_class in ["Camera", "Image"] or "Camera" in name or "Video" in name) and "USB" in device.Description:
                cameras.append(name)
        return cameras
    except Exception as e:
        return [f"Error: {e}"]

if __name__ == "__main__":
    names = get_possible_camera_names()
    print(f"Found Cameras: {names}")
