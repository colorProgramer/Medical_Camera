import win32com.client

def debug_usb_devices():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        print("--- All Potential Video/Camera Devices ---")
        for device in wmi.InstancesOf("Win32_PnPEntity"):
            name = str(device.Caption)
            pnp_class = str(device.PNPClass)
            desc = str(device.Description)
            if "Camera" in name or "Video" in name or pnp_class in ["Camera", "Image"]:
                print(f"Name: {name}")
                print(f"  Class: {pnp_class}")
                print(f"  Desc: {desc}")
                print(f"  Service: {device.Service}")
                print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_usb_devices()
