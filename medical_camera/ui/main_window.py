from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget, QStyle,
    QSlider, QDoubleSpinBox, QSpinBox,
    QStackedWidget
)

from medical_camera.models.device import HIKVISION_PROFILE, USB_PROFILE
from medical_camera.services.actions import ActionDispatcher
from medical_camera.ui.icons import build_icon
from medical_camera.ui.styles import get_app_style
from medical_camera.ui.viewport import FakeViewport


class _DeviceEnumerator(QThread):
    finished = Signal(list, str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        from medical_camera.services.hikvision_service import HikvisionCameraService
        svc = HikvisionCameraService()
        result = svc.enumerate_devices()
        if result.ok and result.data:
            names = [d.display_name for d in result.data]
            self.finished.emit(names, f"已枚举到 {len(result.data)} 台海康设备")
        else:
            msg = result.message if not result.ok else "未枚举到海康设备"
            self.finished.emit(["未发现海康设备"], msg)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.dispatcher = ActionDispatcher()
        self.setWindowTitle("CIQT Medical Camera")
        self.resize(1680, 980)
        self._last_theme = "light"
        self._last_log_count = 0
        self.setStyleSheet(get_app_style("light"))

        self.device_combo: QComboBox
        self.device_label: QLabel
        self.connection_label: QLabel
        self.log_list: QListWidget
        self.status_resolution: QLabel
        self.status_fps: QLabel
        self.status_exposure: QLabel
        self.status_gain: QLabel
        self.status_wb: QLabel
        self.param_group_hik: QGroupBox
        self.param_group_usb: QGroupBox
        self.param_group_usb: QGroupBox
        self.logo_label: QLabel
        self.theme_button: QPushButton
        self.language_button: QPushButton
        self.help_button: QPushButton
        self.connect_button: QPushButton
        self.disconnect_button: QPushButton
        self.start_button: QPushButton
        self.stop_button: QPushButton
        self.save_button: QPushButton
        self.import_button: QPushButton
        self.export_button: QPushButton
        self.load_button: QPushButton
        self.save_config_button: QPushButton
        self.restore_button: QPushButton
        self.config_group: QGroupBox
        self.roi_button: QPushButton
        self.reset_button: QPushButton
        self.capture_button: QPushButton
        self.reset_button: QPushButton
        self.capture_button: QPushButton
        self.start_recognition_button: QPushButton
        self.stop_recognition_button: QPushButton

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())

        body = QFrame()
        body.setObjectName("CenterPanel")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 12)
        body_layout.setSpacing(16)
        body_layout.addWidget(self._build_left_panel(), 3)
        body_layout.addWidget(self._build_center_panel(), 8)
        body_layout.addWidget(self._build_right_panel(), 3)
        root.addWidget(body, 1)

        root.addWidget(self._build_status_bar())

        self._setup_poller()
        self._setup_param_sync_timer()
        self._apply_state()
        self._start_device_enumeration()

    def _setup_poller(self) -> None:
        from medical_camera.ui.frame_poller import HikvisionFramePoller
        self.poller = HikvisionFramePoller(self.dispatcher)
        self.poller.frame_ready.connect(self._on_frame_ready)
        self.poller.stats_ready.connect(self._on_stats_ready)

    def _setup_param_sync_timer(self) -> None:
        self._param_sync_timer = QTimer(self)
        self._param_sync_timer.setInterval(2000)
        self._param_sync_timer.timeout.connect(self._sync_hik_params)

    def _sync_hik_params(self) -> None:
        state = self.dispatcher.state
        if state.current_profile.key == "hikvision" and state.connected:
            self._dispatch("sync_hik_params")

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(14)

        badge = QFrame()
        badge.setObjectName("BrandBadge")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(12, 10, 16, 10)
        badge_layout.setSpacing(12)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(42, 42)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setPixmap(self._load_logo_pixmap())
        badge_layout.addWidget(self.logo_label)

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setContentsMargins(0, 0, 0, 0)
        brand_text_layout.setSpacing(2)
        brand = QLabel("CIQT 医疗相机")
        brand.setObjectName("BrandTitle")
        brand_subtitle = QLabel("ENDOSCOPY CONTROL WORKSTATION")
        brand_subtitle.setObjectName("BrandSubtitle")
        brand_text_layout.addWidget(brand)
        brand_text_layout.addWidget(brand_subtitle)
        badge_layout.addLayout(brand_text_layout)
        layout.addWidget(badge)
        layout.addStretch(1)

        status_pill = QFrame()
        status_pill.setObjectName("InfoPill")
        status_layout = QHBoxLayout(status_pill)
        status_layout.setContentsMargins(14, 10, 14, 10)
        status_layout.setSpacing(10)

        self.connection_label = QLabel("未连接")
        self.connection_label.setStyleSheet("color:#d35d6e; font-weight:700;")
        status_layout.addWidget(self.connection_label)

        self.device_label = QLabel("设备类型：海康工业相机")
        status_layout.addWidget(self.device_label)
        layout.addWidget(status_pill)

        self.theme_button = QPushButton("主题")
        self.theme_button.setObjectName("TopIconButton")
        self.theme_button.clicked.connect(lambda: self._dispatch("toggle_theme"))
        layout.addWidget(self.theme_button)

        self.language_button = QPushButton("语言")
        self.language_button.setObjectName("TopIconButton")
        layout.addWidget(self.language_button)

        self.help_button = QPushButton("帮助")
        self.help_button.setObjectName("TopIconButton")
        layout.addWidget(self.help_button)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("SidePanel")
        panel.setMinimumWidth(340)
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)

        layout.addWidget(self._build_device_group())
        
        self.param_stack = QStackedWidget()
        
        # Hikvision Page (Index 0)
        self.param_group_hik = self._build_hik_params_group()
        self.param_stack.addWidget(self.param_group_hik)
        
        # USB Page (Index 1)
        usb_page = QWidget()
        usb_layout = QVBoxLayout(usb_page)
        usb_layout.setContentsMargins(0, 0, 0, 0)
        usb_layout.setSpacing(14)
        
        self.param_group_usb = self._build_usb_params_group()
        usb_layout.addWidget(self.param_group_usb)
        
        self.config_group = self._build_config_group()
        usb_layout.addWidget(self.config_group)
        
        usb_layout.addStretch(1)
        self.param_stack.addWidget(usb_page)
        
        layout.addWidget(self.param_stack)
        layout.addStretch(1)
        return panel

    def _build_device_group(self) -> QWidget:
        group = QGroupBox("设备与采集")
        layout = QVBoxLayout(group)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("设备类型"))
        self.device_combo = QComboBox()
        self.device_combo.addItem(HIKVISION_PROFILE.title, HIKVISION_PROFILE.key)
        self.device_combo.addItem(USB_PROFILE.title, USB_PROFILE.key)
        self.device_combo.currentIndexChanged.connect(self._on_device_profile_changed)
        type_row.addWidget(self.device_combo, 1)
        layout.addLayout(type_row)

        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel("设备列表"))
        self.refresh_device_button = QPushButton()
        self.refresh_device_button.setObjectName("RefreshDeviceButton")
        self.refresh_device_button.setToolTip("刷新设备列表")
        self.refresh_device_button.clicked.connect(lambda: self._dispatch("refresh_devices"))
        dev_row.addStretch(1)
        dev_row.addWidget(self.refresh_device_button)
        layout.addLayout(dev_row)

        self.device_selector = QComboBox()
        self.device_selector.currentIndexChanged.connect(self._on_device_selector_changed)
        layout.addWidget(self.device_selector)

        button_grid = QGridLayout()
        self.connect_button = QPushButton("连接相机")
        self.connect_button.setObjectName("PrimaryButton")
        self.connect_button.clicked.connect(lambda: self._dispatch("connect_device"))
        self.disconnect_button = QPushButton("断开")
        self.disconnect_button.clicked.connect(lambda: self._dispatch("disconnect_device"))
        self.start_button = QPushButton("开始采集")
        self.start_button.setObjectName("SuccessButton")
        self.start_button.clicked.connect(lambda: self._dispatch("start_collection"))
        self.stop_button = QPushButton("停止采集")
        self.stop_button.setObjectName("DangerButton")
        self.stop_button.clicked.connect(lambda: self._dispatch("stop_collection"))
        self.save_button = QPushButton("保存图片")
        self.save_button.clicked.connect(lambda: self._dispatch("save_image"))

        button_grid.addWidget(self.connect_button, 0, 0)
        button_grid.addWidget(self.disconnect_button, 0, 1)
        button_grid.addWidget(self.start_button, 1, 0)
        button_grid.addWidget(self.stop_button, 1, 1)
        button_grid.addWidget(self.save_button, 2, 0, 1, 2)
        layout.addLayout(button_grid)
        return group

    def _build_hik_params_group(self) -> QGroupBox:
        group = QGroupBox("海康相机参数")
        layout = QGridLayout(group)
        
        # Read-only fields
        self.hik_res_label = QLineEditLike("--")
        self.hik_fps_label = QLineEditLike("--")
        
        layout.addWidget(self._field_label("分辨率"), 0, 0)
        layout.addWidget(self.hik_res_label, 0, 1, 1, 2)
        
        layout.addWidget(self._field_label("帧率(FPS)"), 1, 0)
        layout.addWidget(self.hik_fps_label, 1, 1, 1, 2)
        
        # Editable fields
        self.hik_exposure_slider = QSlider(Qt.Horizontal)
        self.hik_exposure_spin = QDoubleSpinBox()
        self.hik_exposure_spin.setDecimals(0)
        
        self.hik_gain_slider = QSlider(Qt.Horizontal)
        self.hik_gain_spin = QDoubleSpinBox()
        self.hik_gain_spin.setDecimals(1)
        self.hik_gain_spin.setSingleStep(1.0)
        
        self.hik_wb_selector = QComboBox()
        self.hik_wb_selector.addItems(["Red", "Green", "Blue"])
        
        self.hik_wb_slider = QSlider(Qt.Horizontal)
        self.hik_wb_spin = QSpinBox()

        
        self.hik_auto_exposure = QCheckBox("自动曝光")
        self.hik_auto_gain = QCheckBox("自动增益")
        self.hik_auto_wb = QCheckBox("自动白平衡")

        # Layout addition
        row = 2
        layout.addWidget(self._field_label("曝光(us)"), row, 0)
        layout.addWidget(self.hik_exposure_slider, row, 1)
        layout.addWidget(self.hik_exposure_spin, row, 2)
        row += 1
        
        layout.addWidget(self._field_label("增益(dB)"), row, 0)
        layout.addWidget(self.hik_gain_slider, row, 1)
        layout.addWidget(self.hik_gain_spin, row, 2)
        row += 1
        
        layout.addWidget(self._field_label("白平衡通道"), row, 0)
        layout.addWidget(self.hik_wb_selector, row, 1, 1, 2)
        row += 1
        
        layout.addWidget(self._field_label("白平衡值"), row, 0)
        layout.addWidget(self.hik_wb_slider, row, 1)
        layout.addWidget(self.hik_wb_spin, row, 2)
        row += 1
        
        # Auto modes
        auto_layout = QHBoxLayout()
        auto_layout.setSpacing(20)
        auto_layout.addWidget(self.hik_auto_exposure)
        auto_layout.addWidget(self.hik_auto_gain)
        auto_layout.addWidget(self.hik_auto_wb)
        auto_layout.addStretch(1)
        layout.addLayout(auto_layout, row, 1, 1, 2)
        row += 1
        
        # Action buttons row
        btn_layout = QHBoxLayout()
        self.import_button = QPushButton("导入 mfs")
        self.export_button = QPushButton("导出 mfs")
        self.import_button.clicked.connect(self._on_import_mfs)
        self.export_button.clicked.connect(self._on_export_mfs)
        btn_layout.addWidget(self.import_button)
        btn_layout.addWidget(self.export_button)
        layout.addLayout(btn_layout, row, 0, 1, 3)
        
        # Set column stretches for alignment
        layout.setColumnStretch(0, 0) # Labels
        layout.setColumnStretch(1, 1) # Sliders/Wide controls
        layout.setColumnStretch(2, 0) # Value boxes
        
        # UI internal synchronization
        def sync_slider_spin(slider, spin, multiplier=1):
            if isinstance(spin, QDoubleSpinBox):
                slider.valueChanged.connect(lambda v: spin.setValue(v / multiplier))
                spin.valueChanged.connect(lambda v: slider.setValue(int(v * multiplier)))
            else:
                slider.valueChanged.connect(lambda v: spin.setValue(int(v / multiplier)))
                spin.valueChanged.connect(lambda v: slider.setValue(int(v * multiplier)))

        sync_slider_spin(self.hik_exposure_slider, self.hik_exposure_spin, 1)
        sync_slider_spin(self.hik_gain_slider, self.hik_gain_spin, 10)
        sync_slider_spin(self.hik_wb_slider, self.hik_wb_spin, 1)
        
        # Dispatch actions
        def try_dispatch(action, payload):
            self._dispatch(action, payload)

        self.hik_exposure_slider.sliderReleased.connect(lambda: try_dispatch("set_hik_exposure", {"value": self.hik_exposure_spin.value()}))
        self.hik_exposure_spin.editingFinished.connect(lambda: try_dispatch("set_hik_exposure", {"value": self.hik_exposure_spin.value()}))
        
        self.hik_gain_slider.sliderReleased.connect(lambda: try_dispatch("set_hik_gain", {"value": self.hik_gain_spin.value()}))
        self.hik_gain_spin.editingFinished.connect(lambda: try_dispatch("set_hik_gain", {"value": self.hik_gain_spin.value()}))
        
        self.hik_wb_selector.currentIndexChanged.connect(lambda: self._apply_state())
        
        def dispatch_wb_ratio():
            ch = self.hik_wb_selector.currentText().lower()
            try_dispatch("set_hik_balance_ratio", {"channel": ch, "value": self.hik_wb_spin.value()})
            
        self.hik_wb_slider.sliderReleased.connect(dispatch_wb_ratio)
        self.hik_wb_spin.editingFinished.connect(dispatch_wb_ratio)
        
        self.hik_auto_exposure.clicked.connect(lambda: try_dispatch("set_hik_exposure_auto", {"value": self.hik_auto_exposure.isChecked()}))
        self.hik_auto_gain.clicked.connect(lambda: try_dispatch("set_hik_gain_auto", {"value": self.hik_auto_gain.isChecked()}))
        self.hik_auto_wb.clicked.connect(lambda: try_dispatch("set_hik_white_balance_auto", {"value": self.hik_auto_wb.isChecked()}))

        return group

    def _build_usb_params_group(self) -> QGroupBox:
        group = QGroupBox("USB 相机参数")
        layout = QGridLayout(group)
        layout.addWidget(self._field_label("分辨率"), 0, 0)
        resolution = QComboBox()
        resolution.addItems(["1920 x 1080", "1280 x 720", "640 x 480"])
        layout.addWidget(resolution, 0, 1)

        layout.addWidget(self._field_label("像素格式"), 1, 0)
        pixel_format = QComboBox()
        pixel_format.addItems(["MJPG", "YUY2"])
        layout.addWidget(pixel_format, 1, 1)

        layout.addWidget(self._field_label("帧率(FPS)"), 2, 0)
        fps = QComboBox()
        fps.addItems(["60", "30", "25"])
        layout.addWidget(fps, 2, 1)
        return group

    def _build_config_group(self) -> QWidget:
        self.config_group = QGroupBox("配置管理")
        layout = QGridLayout(self.config_group)
        self.load_button = QPushButton("加载配置")
        self.save_config_button = QPushButton("保存配置")
        self.restore_button = QPushButton("恢复默认")
        self.restore_button.setObjectName("GhostButton")
        layout.addWidget(self.load_button, 0, 0)
        layout.addWidget(self.save_config_button, 0, 1)
        layout.addWidget(self.restore_button, 1, 0, 1, 2)
        return self.config_group

    def _build_center_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("CenterPanel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        viewport_card = QFrame()
        viewport_card.setObjectName("Card")
        viewport_layout = QVBoxLayout(viewport_card)
        viewport_layout.setContentsMargins(12, 12, 12, 12)
        viewport_layout.addWidget(self._section_title("实时画面"))
        self.viewport = FakeViewport()
        viewport_layout.addWidget(self.viewport, 1)

        controls = QHBoxLayout()
        self.roi_button = QPushButton("ROI 选区")
        self.roi_button.setObjectName("GhostButton")
        zoom_out = QPushButton("−")
        zoom_out.setObjectName("CompactButton")
        zoom_in = QPushButton("+")
        zoom_in.setObjectName("CompactButton")
        zoom_label = QLabel("1.0x")
        zoom_label.setObjectName("ValueBadge")
        self.reset_button = QPushButton("复位")
        self.reset_button.setObjectName("GhostButton")
        self.reset_button.clicked.connect(lambda: self._dispatch("reset_view"))
        self.capture_button = QPushButton("截图")
        self.capture_button.clicked.connect(lambda: self._dispatch("save_image"))
        for widget in (self.roi_button, zoom_out, zoom_label, zoom_in, self.reset_button, self.capture_button):
            controls.addWidget(widget)
        controls.addStretch(1)
        viewport_layout.addLayout(controls)
        layout.addWidget(viewport_card, 1)

        layout.addWidget(self._build_log_panel(), 1)
        return panel

    def _build_log_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("日志信息"))
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        return card

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RightPanel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)
        layout.addWidget(self._build_recognition_group())
        layout.addWidget(self._build_overlay_group())
        layout.addStretch(1)
        return panel

    def _build_recognition_group(self) -> QWidget:
        group = QGroupBox("识别控制")
        layout = QVBoxLayout(group)

        layout.addWidget(self._field_label("识别区域"))
        scope_row = QHBoxLayout()
        full_radio = QRadioButton("全图")
        roi_radio = QRadioButton("ROI 区域")
        full_radio.setChecked(True)
        full_radio.toggled.connect(lambda checked: checked and self._dispatch("set_detection_scope", {"value": "full"}))
        roi_radio.toggled.connect(lambda checked: checked and self._dispatch("set_detection_scope", {"value": "roi"}))
        scope_row.addWidget(full_radio)
        scope_row.addWidget(roi_radio)
        layout.addLayout(scope_row)

        layout.addWidget(self._field_label("识别模式"))
        mode_row = QHBoxLayout()
        single_radio = QRadioButton("单次识别")
        realtime_radio = QRadioButton("实时识别")
        single_radio.setChecked(True)
        single_radio.toggled.connect(lambda checked: checked and self._dispatch("set_recognition_mode", {"value": "single"}))
        realtime_radio.toggled.connect(lambda checked: checked and self._dispatch("set_recognition_mode", {"value": "real_time"}))
        mode_row.addWidget(single_radio)
        mode_row.addWidget(realtime_radio)
        layout.addLayout(mode_row)

        layout.addWidget(self._field_label("视场类型"))
        shape_row = QHBoxLayout()
        circle_radio = QRadioButton("圆视场")
        rect_radio = QRadioButton("矩形视场")
        circle_radio.setChecked(True)
        circle_radio.toggled.connect(lambda checked: checked and self._dispatch("set_field_shape", {"value": "circle"}))
        rect_radio.toggled.connect(lambda checked: checked and self._dispatch("set_field_shape", {"value": "rectangle"}))
        shape_row.addWidget(circle_radio)
        shape_row.addWidget(rect_radio)
        layout.addLayout(shape_row)

        layout.addWidget(self._field_label("图案模式"))
        pattern_combo = QComboBox()
        pattern_combo.addItem("黑底白图案", "dark_bg")
        pattern_combo.addItem("白底黑图案", "light_bg")
        pattern_combo.currentIndexChanged.connect(
            lambda: self._dispatch("set_pattern_mode", {"value": pattern_combo.currentData()})
        )
        layout.addWidget(pattern_combo)

        self.start_recognition_button = QPushButton("开始识别")
        self.start_recognition_button.setObjectName("PrimaryButton")
        self.start_recognition_button.clicked.connect(lambda: self._dispatch("start_recognition"))
        self.stop_recognition_button = QPushButton("停止识别")
        self.stop_recognition_button.setObjectName("GhostButton")
        self.stop_recognition_button.clicked.connect(lambda: self._dispatch("stop_recognition"))
        layout.addWidget(self.start_recognition_button)
        layout.addWidget(self.stop_recognition_button)
        return group

    def _build_overlay_group(self) -> QWidget:
        group = QGroupBox("显示叠加")
        layout = QVBoxLayout(group)
        items = [
            "圆视场边界",
            "70%视场圆",
            "矩形视场(ROI)",
            "视场中心十字线",
            "画面中心米字线",
        ]
        for text in items:
            checkbox = QCheckBox(text)
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
        layout.addWidget(QCheckBox("n%视场圆"))
        return group

    def _build_status_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("StatusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(16)

        self.status_resolution = QLabel()
        self.status_fps = QLabel()
        self.status_exposure = QLabel()
        self.status_gain = QLabel()
        self.status_wb = QLabel()

        for widget in (
            self._field_label("状态栏"),
            self.status_resolution,
            self.status_fps,
            self.status_exposure,
            self.status_gain,
            self.status_wb,
        ):
            layout.addWidget(widget)
        layout.addStretch(1)
        layout.addWidget(QLabel("当前模式：ROI编辑"))
        return bar

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _value_badge(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("ValueBadge")
        return label

    def _load_logo_pixmap(self) -> QPixmap:
        branding_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "branding"
        for file_name in ("company_logo.png", "company_logo.svg", "company_logo.jpg"):
            file_path = branding_dir / file_name
            if file_path.exists():
                pixmap = QPixmap(str(file_path))
                if not pixmap.isNull():
                    return pixmap.scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        fallback = self.style().standardIcon(QStyle.SP_ComputerIcon)
        return fallback.pixmap(30, 30)

    def _on_device_profile_changed(self) -> None:
        state = self.dispatcher.state
        if state.connected:
            self.device_combo.blockSignals(True)
            for i in range(self.device_combo.count()):
                if self.device_combo.itemData(i) == state.current_profile.key:
                    self.device_combo.setCurrentIndex(i)
                    break
            self.device_combo.blockSignals(False)
            self._dispatch("append_log", {"category": "警告", "message": "设备已连接，禁止切换设备类型"})
            return

        device_key = self.device_combo.currentData()
        self.dispatcher.switch_device_type(device_key)
        self._apply_state()
        if device_key == "hikvision":
            self._start_device_enumeration()

    def _start_device_enumeration(self) -> None:
        worker = _DeviceEnumerator(self)
        worker.finished.connect(self._on_device_enumerated)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _on_device_enumerated(self, devices: list[str], log_msg: str) -> None:
        if self.dispatcher.state.current_profile.key != "hikvision":
            return
        self.dispatcher.apply_device_list(devices, log_msg)
        self._apply_state()

    def _on_device_selector_changed(self, index: int) -> None:
        if index >= 0:
            self.dispatcher.dispatch("select_device", {"value": index})

    def _dispatch(self, action: str, payload: dict | None = None) -> None:
        self.dispatcher.dispatch(action, payload)
        self._apply_state()
        if action == "refresh_devices" and self.dispatcher.state.current_profile.key == "hikvision":
            self._start_device_enumeration()

        if action == "connect_device":
            self._param_sync_timer.start()
        elif action == "start_collection":
            self.poller.start()
        elif action == "stop_collection":
            self.poller.stop()
        elif action == "disconnect_device":
            self.poller.stop()
            self._param_sync_timer.stop()
            self.viewport.clear_frame()

    def _on_frame_ready(self, frame) -> None:
        self.viewport.set_frame(frame.data, frame.width, frame.height, frame.byte_count, frame.frame_number, frame.pixel_type)

    def _on_stats_ready(self, fps: float, frame_number: int) -> None:
        self.viewport.set_display_fps(fps)

    def _apply_state(self) -> None:
        state = self.dispatcher.state
        if state.theme != self._last_theme:
            self._last_theme = state.theme
            self.setStyleSheet(get_app_style(state.theme))
            self._apply_icons(state.theme)
        self.device_selector.blockSignals(True)
        self.device_selector.clear()
        devices = state.available_devices if state.available_devices else [state.current_profile.sample_device]
        self.device_selector.addItems(devices)
        idx = min(max(state.selected_device_index, 0), self.device_selector.count() - 1)
        self.device_selector.setCurrentIndex(idx)
        self.device_selector.blockSignals(False)
        self.device_label.setText(f"设备类型：{state.current_profile.title}")
        self.connection_label.setText("已连接" if state.connected else "未连接")
        self.connection_label.setStyleSheet(
            "color:#1f9f68; font-weight:700;" if state.connected else "color:#d35d6e; font-weight:700;"
        )

        caps = state.current_profile.capabilities
        if caps.supports_exposure or caps.supports_mfs:
            self.param_stack.setCurrentIndex(0)
        else:
            self.param_stack.setCurrentIndex(1)

        self.status_resolution.setText(f"分辨率：{state.resolution_text}")
        self.status_fps.setText(f"帧率：{state.fps_text}")
        self.status_exposure.setVisible(caps.supports_exposure)
        self.status_gain.setVisible(caps.supports_gain)
        self.status_wb.setVisible(caps.supports_white_balance)
        self.status_exposure.setText(f"曝光：{state.exposure_text}")
        self.status_gain.setText(f"增益：{state.gain_text}")
        self.status_wb.setText(f"白平衡：{state.white_balance_text}")

        if caps.supports_exposure or caps.supports_mfs:
            self.hik_res_label.setText(state.resolution_text)
            self.hik_fps_label.setText(state.fps_text)
            
            hik_params = state.hik_params
            if hik_params:
                def _update_spin_slider(spin, slider, value_dict, multiplier=1):
                    if value_dict and value_dict.get("available"):
                        slider.blockSignals(True)
                        spin.blockSignals(True)
                        
                        cur = value_dict.get("current", 0)
                        min_v = value_dict.get("minimum", 0)
                        max_v = value_dict.get("maximum", 100)
                        
                        spin.setRange(min_v, max_v)
                        
                        s_min = int(min_v * multiplier)
                        s_max = int(max_v * multiplier)
                        if s_max > 2147483647:
                            s_max = 2147483647
                        slider.setRange(s_min, s_max)
                        
                        if not slider.isSliderDown():
                            spin.setValue(cur)
                            slider.setValue(int(cur * multiplier))
                        
                        slider.blockSignals(False)
                        spin.blockSignals(False)
                        
                        slider.setEnabled(True)
                        spin.setEnabled(True)
                    else:
                        slider.setEnabled(False)
                        spin.setEnabled(False)

                def _update_checkbox(cb, value_dict):
                    if value_dict and value_dict.get("available"):
                        cb.blockSignals(True)
                        # The enum values typically have >0 as 'continuous' or 'once' and 0 as 'off'
                        cb.setChecked(value_dict.get("current", 0) > 0)
                        cb.blockSignals(False)
                        cb.setEnabled(True)
                    else:
                        cb.setEnabled(False)

                _update_spin_slider(self.hik_exposure_spin, self.hik_exposure_slider, hik_params.get("exposure"), 1)
                _update_spin_slider(self.hik_gain_spin, self.hik_gain_slider, hik_params.get("gain"), 10)
                current_wb_ch = self.hik_wb_selector.currentText().lower()
                wb_key = f"balance_ratio_{current_wb_ch}"
                _update_spin_slider(self.hik_wb_spin, self.hik_wb_slider, hik_params.get(wb_key), 1)

                _update_checkbox(self.hik_auto_exposure, hik_params.get("exposure_auto"))
                _update_checkbox(self.hik_auto_gain, hik_params.get("gain_auto"))
                _update_checkbox(self.hik_auto_wb, hik_params.get("white_balance_auto"))
                
                if self.hik_auto_exposure.isChecked():
                    self.hik_exposure_slider.setEnabled(False)
                    self.hik_exposure_spin.setEnabled(False)
                if self.hik_auto_gain.isChecked():
                    self.hik_gain_slider.setEnabled(False)
                    self.hik_gain_spin.setEnabled(False)
                if self.hik_auto_wb.isChecked():
                    self.hik_wb_selector.setEnabled(False)
                    self.hik_wb_slider.setEnabled(False)
                    self.hik_wb_spin.setEnabled(False)
                else:
                    self.hik_wb_selector.setEnabled(True)

        if len(state.logs) != self._last_log_count:
            self._last_log_count = len(state.logs)
            self.log_list.clear()
            for message in state.logs:
                QListWidgetItem(message, self.log_list)
            self.log_list.scrollToBottom()

    def _apply_icons(self, theme: str) -> None:
        icon_color = "#409eff" if theme == "light" else "#8bc0ff"
        action_color = "#ffffff"
        ghost_color = icon_color

        self.theme_button.setIcon(build_icon("theme", icon_color))
        self.language_button.setIcon(build_icon("language", icon_color))
        self.help_button.setIcon(build_icon("help", icon_color))

        self.connect_button.setIcon(build_icon("connect", action_color))
        self.disconnect_button.setIcon(build_icon("disconnect", icon_color))
        self.start_button.setIcon(build_icon("play", action_color))
        self.stop_button.setIcon(build_icon("stop", action_color))
        self.save_button.setIcon(build_icon("save", action_color))
        self.import_button.setIcon(build_icon("open", action_color))
        self.export_button.setIcon(build_icon("save", action_color))
        self.load_button.setIcon(build_icon("open", action_color))
        self.save_config_button.setIcon(build_icon("save", action_color))
        self.restore_button.setIcon(build_icon("reset", ghost_color))
        self.roi_button.setIcon(build_icon("roi", ghost_color))
        self.reset_button.setIcon(build_icon("reset", ghost_color))
        self.capture_button.setIcon(build_icon("save", action_color))
        self.start_recognition_button.setIcon(build_icon("play", action_color))
        self.stop_recognition_button.setIcon(build_icon("stop", ghost_color))
        self.refresh_device_button.setIcon(build_icon("refresh", icon_color))

    def _on_import_mfs(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入 mfs 文件",
            "",
            "MFS 文件 (*.mfs);;所有文件 (*.*)"
        )
        if file_path:
            self._dispatch("import_mfs", {"file_path": file_path})

    def _on_export_mfs(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 mfs 文件",
            "",
            "MFS 文件 (*.mfs);;所有文件 (*.*)"
        )
        if file_path:
            if not file_path.endswith(".mfs"):
                file_path += ".mfs"
            self._dispatch("export_mfs", {"file_path": file_path})


class QLineEditLike(QLabel):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("ValueBadge")
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
