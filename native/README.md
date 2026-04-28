# native

本目录放项目自己的 C++ 原生封装，不修改 `ReadOnly` 下的海康参考样例。

## 当前内容

1. `medical_camera_hikvision`
   海康 MVS SDK 的项目内封装层。
2. `hikvision_sdk_demo`
   最小示例程序，用于验证 SDK 初始化、枚举、打开、参数读取、`mfs` 保存。

## MVS 目录说明

你当前机器上已确认：

1. `G:\MVS\Development`
   这是开发目录。
   这里有 `MvCameraControl.h` 和 `MvCameraControl.lib`，用于编译。

2. `C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64`
   这是运行库目录。
   这里有 `MvCameraControl.dll` 等运行时依赖，供程序运行使用。

## 编译前提

当前工程使用 CMake，配置时需要显式传入：

```powershell
cmake -S native -B native\build -DMVS_SDK_ROOT="G:/MVS/Development"
cmake --build native\build --config Release
```

## 当前封装能力

已经覆盖以下接口：

1. SDK 初始化/反初始化
2. 设备枚举
3. 打开/关闭设备
4. 开始/停止采集
5. 获取一帧图像
6. 分辨率宽高当前值与范围
7. 像素格式当前值与支持值列表
8. 曝光当前值与范围
9. 增益当前值与范围
10. 帧率当前值与范围
11. 自动曝光/自动增益/自动白平衡状态与支持值
12. RGB 白平衡比例范围与设置
13. 触发模式/触发源查询与设置
14. ReverseX/ReverseY 查询与设置
15. DeviceUserID 查询与设置
16. GigE 最优包大小与包大小设置
17. `mfs` 特征文件保存/加载

## 说明

这层封装的目标不是替代全部 MVS API，而是优先覆盖本项目 UI 和应用层直接需要的能力，尤其是：

1. 当前值查询
2. 可配置范围查询
3. 支持枚举值查询
4. 参数设置
5. 采集主流程
