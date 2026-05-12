#include "usb_utils.h"

#include <windows.h>
#include <dshow.h>
#include <vector>
#include <string>

#pragma comment(lib, "strmiids.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")

extern "C" {

USB_API int mc_usb_get_device_count() {
    HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    int count = 0;

    ICreateDevEnum* pDevEnum = NULL;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
                          IID_ICreateDevEnum, (void**)&pDevEnum);

    if (SUCCEEDED(hr)) {
        IEnumMoniker* pEnum = NULL;
        hr = pDevEnum->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &pEnum, 0);

        if (hr == S_OK) {
            IMoniker* pMoniker = NULL;
            while (pEnum->Next(1, &pMoniker, NULL) == S_OK) {
                count++;
                pMoniker->Release();
            }
            pEnum->Release();
        }
        pDevEnum->Release();
    }

    CoUninitialize();
    return count;
}

USB_API int mc_usb_get_device_name(int index, wchar_t* buffer, int capacity) {
    if (!buffer || capacity <= 0) return -1;

    HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    int current_index = 0;
    int result = -2; // Not found

    ICreateDevEnum* pDevEnum = NULL;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
                          IID_ICreateDevEnum, (void**)&pDevEnum);

    if (SUCCEEDED(hr)) {
        IEnumMoniker* pEnum = NULL;
        hr = pDevEnum->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &pEnum, 0);

        if (hr == S_OK) {
            IMoniker* pMoniker = NULL;
            bool found = false;
            while (pEnum->Next(1, &pMoniker, NULL) == S_OK) {
                if (current_index == index) {
                    IPropertyBag* pPropBag;
                    hr = pMoniker->BindToStorage(0, 0, IID_IPropertyBag, (void**)&pPropBag);
                    if (SUCCEEDED(hr)) {
                        VARIANT var;
                        VariantInit(&var);
                        hr = pPropBag->Read(L"FriendlyName", &var, 0);
                        if (SUCCEEDED(hr)) {
                            wcsncpy_s(buffer, capacity, var.bstrVal, _TRUNCATE);
                            result = 0; // Success
                            found = true;
                        }
                        VariantClear(&var);
                        pPropBag->Release();
                    }
                }
                pMoniker->Release();
                if (found) break;
                current_index++;
            }
            pEnum->Release();
        }
        pDevEnum->Release();
    }

    CoUninitialize();
    return result;
}

}
