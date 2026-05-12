import win32com.client

def get_usb_camera_names():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        cameras = []
        # PNPClass 'Camera' is common for built-in and modern USB cams
        # PNPClass 'Image' is often used for older scanners/cameras
        for device in wmi.InstancesOf("Win32_PnPEntity"):
            pnp_class = str(device.PNPClass)
            if pnp_class in ["Camera", "Image"] and device.ConfigManagerErrorCode == 0:
                cameras.append(device.Caption)
        return cameras
    except Exception as e:
        return [f"Error: {e}"]

if __name__ == "__main__":
    names = get_usb_camera_names()
    print(f"Found Cameras: {names}")
