# Medical Camera - 医疗内窥镜控制工作站

![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-green.svg)
![Framework](https://img.shields.io/badge/framework-PySide6-orange.svg)

Medical Camera 是一款专为医疗内窥镜设计的专业图像采集与控制工作站。它提供了高性能的实时画面显示、精准的相机参数调节以及多种医疗视觉辅助功能。

## 🌟 核心功能

### 1. 多设备支持

* **海康工业相机**：深度集成海康 SDK，支持高性能工业级数据采集。
* **标准 USB 相机**：兼容 UVC 协议的通用医疗/内窥镜相机。

### 2. 精准的相机控制

* **图像参数调节**：支持手动/自动曝光、增益调节。
* **白平衡管理**：支持 R/G/B 分通道独立调节及自动 white balance。
* **配置导入导出**：支持海康相机 `.mfs` 配置文件的导入与导出。

### 3. 专业视觉辅助 (Overlay)

* **实时视场控制**：支持圆视场 (Circular FOV) 和矩形视场 (Rectangular FOV)。
* **辅助线叠加**：提供 70% 视场圆、视场中心十字线、画面中心米字线等医疗级参考线。
* **ROI 区域**：支持交互式的感兴趣区域 (ROI) 选择。

### 4. 识别与分析

* **智能化识别**：支持单次识别与实时识别模式。
* **图像采集**：一键保存原始图像或高质量截图。

### 5. 现代化 UI/UX

* **专业界面设计**：基于 PySide6 构建，界面简洁、专业。
* **深/浅色模式**：支持主题一键切换，适应不同的医疗办公环境。
* **实时日志**：完整的操作与状态日志系统。

## 🚀 快速开始

### 环境要求

* Python 3.8 或以上版本
* [推荐] 创建虚拟环境：`python -m venv venv`

### 安装依赖

```bash
pip install PySide6 numpy opencv-python
# 如果使用海康相机，请确保已安装海康工业相机驱动 (MVS)
```

### 运行程序

```bash
python main.py
```

## 📂 项目结构

```text
Medical_Camera/
├── assets/             # 资源文件（图标、品牌 Logo）
├── medical_camera/     # 源码目录
│   ├── ui/             # UI 组件与样式定义
│   ├── services/       # 相机底层服务与逻辑
│   ├── bridges/        # 逻辑与 UI 的桥接层
│   └── models/         # 数据模型与配置
├── native/             # C++ 底层实现
├── scripts/            # 辅助工具脚本
├── main.py             # 入口文件
└── .ignore             # Git 忽略配置
```

## 🛠 开发与反馈

如果您在使用过程中遇到任何问题或有改进建议，欢迎提交 Issue。

**Dev Team**
