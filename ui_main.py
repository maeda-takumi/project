# ui_main.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize, QDateTime
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QCheckBox, QPushButton,
    QComboBox, QSpinBox, QMessageBox, QLabel,
    QStackedWidget, QFrame, QToolButton, QDateTimeEdit, QTableWidget,
    QAbstractItemView
)

from style import APP_QSS


class MainWindow(QMainWindow):
    ORDER_COL_SYMBOL = 0
    ORDER_COL_PRODUCT = 1
    ORDER_COL_SIDE = 2
    ORDER_COL_ENTRY_TYPE = 3
    ORDER_COL_LIMIT_PRICE = 4
    ORDER_COL_SL_DIFF = 5
    ORDER_COL_TP_DIFF = 6
    # ロジック側が拾うためのシグナル
    request_save_api = Signal()
    request_load_api = Signal()
    request_submit_orders = Signal()
    request_clear_orders = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("kabuS Auto Trader (Prototype)")
        self.resize(1200, 720)

        root = QWidget()
        root.setStyleSheet(APP_QSS)
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # --- Top Nav Card (Option / Kabu) ---
        self.top_nav = self._build_top_nav()
        layout.addWidget(self.top_nav)

        # --- Pages ---
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)

        # Page 0: 設定（API設定）
        self.page_settings = QWidget()
        p0 = QVBoxLayout(self.page_settings)
        p0.setContentsMargins(0, 0, 0, 0)
        p0.setSpacing(14)
        self.api_group = self._build_api_group()
        p0.addWidget(self.api_group)
        p0.addStretch(1)

        # Page 1: 自動取引（注文設定）
        self.page_trading = QWidget()
        p1 = QVBoxLayout(self.page_trading)
        p1.setContentsMargins(0, 0, 0, 0)
        p1.setSpacing(14)
        self.order_group = self._build_order_group()
        p1.addWidget(self.order_group, 1)

        self.pages.addWidget(self.page_settings)
        self.pages.addWidget(self.page_trading)

        # --- Status ---
        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        self._wire_ui_events()

        # 初期表示：自動取引（好みで settings にしてもOK）
        self.switch_page(1)

    # ========= Top Nav =========
    def _build_top_nav(self) -> QFrame:
        card = QFrame()
        card.setObjectName("topNavCard")
        card.setFrameShape(QFrame.NoFrame)

        row = QHBoxLayout(card)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        self.btn_nav_settings = QToolButton()
        self.btn_nav_settings.setObjectName("navBtn")
        self.btn_nav_settings.setText("設定")
        self.btn_nav_settings.setIcon(QIcon("img/option.png"))
        self.btn_nav_settings.setIconSize(QSize(26, 26))
        self.btn_nav_settings.setCursor(Qt.PointingHandCursor)

        self.btn_nav_trading = QToolButton()
        self.btn_nav_trading.setObjectName("navBtn")
        self.btn_nav_trading.setText("自動取引")
        self.btn_nav_trading.setIcon(QIcon("img/kabu.png"))
        self.btn_nav_trading.setIconSize(QSize(26, 26))
        self.btn_nav_trading.setCursor(Qt.PointingHandCursor)

        row.addWidget(self.btn_nav_settings)
        row.addWidget(self.btn_nav_trading)
        row.addStretch(1)

        # 右側に小さく説明ラベル（任意）
        hint = QLabel("上のボタンで画面を切り替え")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        row.addWidget(hint)

        # click
        self.btn_nav_settings.clicked.connect(lambda: self.switch_page(0))
        self.btn_nav_trading.clicked.connect(lambda: self.switch_page(1))

        return card

    def switch_page(self, index: int):
        self.pages.setCurrentIndex(index)
        # active 表示
        self.btn_nav_settings.setProperty("active", index == 0)
        self.btn_nav_trading.setProperty("active", index == 1)
        # QSS反映
        self.btn_nav_settings.style().unpolish(self.btn_nav_settings)
        self.btn_nav_settings.style().polish(self.btn_nav_settings)
        self.btn_nav_trading.style().unpolish(self.btn_nav_trading)
        self.btn_nav_trading.style().polish(self.btn_nav_trading)

    # ========= API SETTINGS（中身は前のまま） =========
    def _build_api_group(self) -> QGroupBox:
        g = QGroupBox("API設定")
        form = QFormLayout(g)

        self.api_name = QLineEdit()
        self.api_base_url = QLineEdit()
        self.api_password = QLineEdit()
        self.api_password.setEchoMode(QLineEdit.Password)
        self.api_active = QCheckBox("有効")
        self.api_active.setChecked(True)

        form.addRow("名前", self.api_name)
        form.addRow("Base URL", self.api_base_url)
        form.addRow("APIパスワード", self.api_password)
        form.addRow("", self.api_active)

        btn_row = QHBoxLayout()
        self.btn_api_load = QPushButton("読込")
        self.btn_api_save = QPushButton("保存")
        self.btn_api_save.setObjectName("primary")  # 青ボタンに
        btn_row.addWidget(self.btn_api_load)
        btn_row.addWidget(self.btn_api_save)
        form.addRow(btn_row)

        api_hint = QLabel("※ api_accounts の最新(または有効)レコードを読み書きします")
        api_hint.setObjectName("muted")
        api_hint.setWordWrap(True)
        form.addRow(api_hint)

        return g

    # ========= ORDER SETTINGS（中身は前のまま） =========
    def _build_order_group(self) -> QGroupBox:
        g = QGroupBox("注文設定")
        v = QVBoxLayout(g)

        self.orders_table = QTableWidget(0, 7)
        self.orders_table.setHorizontalHeaderLabels([
            "銘柄コード", "信用/現物", "売買", "成行/指値", "指値価格", "損切差額", "利確差額"
        ])
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.orders_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.setShowGrid(True)
        self.orders_table.setAlternatingRowColors(True)
        v.addWidget(self.orders_table)

        row_tools = QHBoxLayout()
        self.btn_add_row = QPushButton("行追加")
        self.btn_remove_row = QPushButton("選択行削除")
        row_tools.addWidget(self.btn_add_row)
        row_tools.addWidget(self.btn_remove_row)
        row_tools.addStretch(1)
        v.addLayout(row_tools)

        run_row = QHBoxLayout()

        self.order_run_mode = QComboBox()
        self.order_run_mode.addItem("即時実行", "immediate")
        self.order_run_mode.addItem("予約実行", "scheduled")
        run_row.addWidget(self._build_form_row("実行方式", self.order_run_mode))

        self.order_scheduled_at = QDateTimeEdit()
        self.order_scheduled_at.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.order_scheduled_at.setDateTime(QDateTime.currentDateTime())
        self.order_scheduled_at.setCalendarPopup(True)
        self.schedule_row = self._build_form_row("実行日時", self.order_scheduled_at)
        run_row.addWidget(self.schedule_row)
        run_row.addStretch(1)
        v.addLayout(run_row)

        hint = QLabel("行追加で複数注文に対応。損切/利確は差額入力（符号は内部で自動付与）")
        hint.setObjectName("muted")
        v.addWidget(hint)

        self.order_error_label = QLabel("")
        self.order_error_label.setObjectName("error")
        self.order_error_label.setWordWrap(True)
        v.addWidget(self.order_error_label)

        tool = QHBoxLayout()
        self.btn_clear = QPushButton("クリア")
        self.btn_clear.setObjectName("danger")
        tool.addWidget(self.btn_clear)
        tool.addStretch(1)

        self.btn_submit = QPushButton("送信（DB保存）")
        self.btn_submit.setObjectName("primary")  # 青
        tool.addWidget(self.btn_submit)
        v.addLayout(tool)

        self._add_order_row()
        self._update_order_field_visibility()
        self._validate_order_form()
        return g

    def _wire_ui_events(self):
        self.btn_api_save.clicked.connect(self.request_save_api.emit)
        self.btn_api_load.clicked.connect(self.request_load_api.emit)

        self.btn_clear.clicked.connect(self.request_clear_orders.emit)
        self.btn_submit.clicked.connect(self.request_submit_orders.emit)

        self.order_run_mode.currentIndexChanged.connect(self._handle_run_mode_change)

        self.btn_add_row.clicked.connect(self._add_order_row)
        self.btn_remove_row.clicked.connect(self._remove_selected_rows)

        self.order_run_mode.currentIndexChanged.connect(self._validate_order_form)
        self.order_scheduled_at.dateTimeChanged.connect(self._validate_order_form)

    def _build_form_row(self, label_text: str, widget: QWidget) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        label = QLabel(label_text)
        label.setMinimumWidth(140)
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return row

    def _update_order_field_visibility(self):
        is_scheduled = self.order_run_mode.currentData() == "scheduled"
        self.schedule_row.setVisible(is_scheduled)

    def _handle_entry_type_change(self):
        sender = self.sender()
        row = self._find_row_for_widget(sender)
        if row < 0:
            return
        self._set_row_limit_state(row)
        self._validate_order_form()

    def _get_row_entry_type(self, row: int) -> str:
        widget = self._get_row_widget(row, self.ORDER_COL_ENTRY_TYPE)
        if isinstance(widget, QComboBox):
            return widget.currentData()
        return "market"

    def _get_row_widget(self, row: int, col: int) -> QWidget | None:
        return self.orders_table.cellWidget(row, col)

    def _find_row_for_widget(self, widget: QWidget | None) -> int:
        if widget is None:
            return -1
        for row in range(self.orders_table.rowCount()):
            for col in range(self.orders_table.columnCount()):
                if self.orders_table.cellWidget(row, col) is widget:
                    return row
        return -1
    def _handle_run_mode_change(self):
        self._update_order_field_visibility()
        self._validate_order_form()

    def _add_order_row(self):
        row = self.orders_table.rowCount()
        self.orders_table.insertRow(row)

        symbol = QLineEdit()
        symbol.textChanged.connect(self._validate_order_form)
        self.orders_table.setCellWidget(row, self.ORDER_COL_SYMBOL, symbol)

        product = QComboBox()
        product.addItem("現物", "cash")
        product.addItem("信用", "margin")
        product.currentIndexChanged.connect(self._validate_order_form)
        self.orders_table.setCellWidget(row, self.ORDER_COL_PRODUCT, product)

        side = QComboBox()
        side.addItem("買", "buy")
        side.addItem("売", "sell")
        side.currentIndexChanged.connect(self._validate_order_form)
        self.orders_table.setCellWidget(row, self.ORDER_COL_SIDE, side)

        entry_type = QComboBox()
        entry_type.addItem("成行", "market")
        entry_type.addItem("指値", "limit")
        entry_type.currentIndexChanged.connect(self._handle_entry_type_change)
        self.orders_table.setCellWidget(row, self.ORDER_COL_ENTRY_TYPE, entry_type)

        limit_price = QSpinBox()
        limit_price.setRange(1, 1_000_000_000)
        limit_price.setValue(1)
        limit_price.setSuffix(" 円")
        limit_price.valueChanged.connect(self._validate_order_form)
        limit_price.setEnabled(False)
        self.orders_table.setCellWidget(row, self.ORDER_COL_LIMIT_PRICE, limit_price)

        sl_diff = QSpinBox()
        sl_diff.setRange(1, 1_000_000_000)
        sl_diff.setValue(1)
        sl_diff.setSuffix(" 円")
        sl_diff.valueChanged.connect(self._validate_order_form)
        self.orders_table.setCellWidget(row, self.ORDER_COL_SL_DIFF, sl_diff)

        tp_diff = QSpinBox()
        tp_diff.setRange(1, 1_000_000_000)
        tp_diff.setValue(1)
        tp_diff.setSuffix(" 円")
        tp_diff.valueChanged.connect(self._validate_order_form)
        self.orders_table.setCellWidget(row, self.ORDER_COL_TP_DIFF, tp_diff)

        self._set_row_limit_state(row)
        self._validate_order_form()

    def _remove_selected_rows(self):
        selected = sorted({idx.row() for idx in self.orders_table.selectionModel().selectedRows()}, reverse=True)
        for row in selected:
            self.orders_table.removeRow(row)
        if self.orders_table.rowCount() == 0:
            self._add_order_row()
        self._validate_order_form()

    def _set_row_limit_state(self, row: int):
        entry_type = self._get_row_entry_type(row)
        limit_widget = self._get_row_widget(row, self.ORDER_COL_LIMIT_PRICE)
        if isinstance(limit_widget, QSpinBox):
            limit_widget.setEnabled(entry_type == "limit")

    def clear_orders(self):
        self.orders_table.setRowCount(0)
        self._add_order_row()
        self.order_run_mode.setCurrentIndex(0)
        self.order_scheduled_at.setDateTime(QDateTime.currentDateTime())
        self._update_order_field_visibility()
        self._validate_order_form()

    def get_orders_payload(self):
        orders = []
        for row in range(self.orders_table.rowCount()):
            symbol_widget = self._get_row_widget(row, self.ORDER_COL_SYMBOL)
            symbol = symbol_widget.text().strip() if isinstance(symbol_widget, QLineEdit) else ""
            if not symbol:
                continue

            product_widget = self._get_row_widget(row, self.ORDER_COL_PRODUCT)
            side_widget = self._get_row_widget(row, self.ORDER_COL_SIDE)
            entry_widget = self._get_row_widget(row, self.ORDER_COL_ENTRY_TYPE)
            limit_widget = self._get_row_widget(row, self.ORDER_COL_LIMIT_PRICE)
            sl_widget = self._get_row_widget(row, self.ORDER_COL_SL_DIFF)
            tp_widget = self._get_row_widget(row, self.ORDER_COL_TP_DIFF)

            entry_type = entry_widget.currentData() if isinstance(entry_widget, QComboBox) else "market"
            side = side_widget.currentData() if isinstance(side_widget, QComboBox) else "buy"
            tp_diff = int(tp_widget.value()) if isinstance(tp_widget, QSpinBox) else 1
            sl_diff = int(sl_widget.value()) if isinstance(sl_widget, QSpinBox) else 1

            if side == "buy":
                tp_signed = tp_diff
                sl_signed = -sl_diff
            else:
                tp_signed = -tp_diff
                sl_signed = sl_diff

            entry_price = None
            if entry_type == "limit" and isinstance(limit_widget, QSpinBox):
                entry_price = int(limit_widget.value())

            orders.append({
                "symbol": symbol,
                "exchange": 9,
                "product": product_widget.currentData() if isinstance(product_widget, QComboBox) else "cash",
                "side": side,
                "qty": 100,
                "entry_type": entry_type,
                "entry_price": entry_price,
                "tp_price": float(tp_signed),
                "sl_trigger_price": float(sl_signed),
                "batch_name": "手動バッチ",
                "memo": "",
                "run_mode": self.order_run_mode.currentData(),
                "scheduled_at": self.order_scheduled_at.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            })

        return orders

    def get_order_validation_errors(self) -> list[str]:
        errors = []
        if self.orders_table.rowCount() == 0:
            errors.append("注文行を追加してください。")
            return errors

        for row in range(self.orders_table.rowCount()):
            symbol_widget = self._get_row_widget(row, self.ORDER_COL_SYMBOL)
            symbol = symbol_widget.text().strip() if isinstance(symbol_widget, QLineEdit) else ""
            if not symbol:
                errors.append(f"{row + 1}行目: 銘柄コードを入力してください。")
                continue

            entry_widget = self._get_row_widget(row, self.ORDER_COL_ENTRY_TYPE)
            entry_type = entry_widget.currentData() if isinstance(entry_widget, QComboBox) else "market"
            limit_widget = self._get_row_widget(row, self.ORDER_COL_LIMIT_PRICE)
            if entry_type == "limit" and isinstance(limit_widget, QSpinBox):
                if limit_widget.value() < 1:
                    errors.append(f"{row + 1}行目: 指値価格は1円以上で指定してください。")

            sl_widget = self._get_row_widget(row, self.ORDER_COL_SL_DIFF)
            if isinstance(sl_widget, QSpinBox) and sl_widget.value() < 1:
                errors.append(f"{row + 1}行目: 損切差額は1円以上で指定してください。")

            tp_widget = self._get_row_widget(row, self.ORDER_COL_TP_DIFF)
            if isinstance(tp_widget, QSpinBox) and tp_widget.value() < 1:
                errors.append(f"{row + 1}行目: 利確差額は1円以上で指定してください。")

        return errors

    def _validate_order_form(self):
        errors = self.get_order_validation_errors()
        if errors:
            self.order_error_label.setText(" / ".join(errors))
            self.btn_submit.setEnabled(False)
        else:
            self.order_error_label.setText("")
            self.btn_submit.setEnabled(True)


    def toast(self, title: str, message: str, error: bool = False):
        self.status_label.setText(message)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Critical if error else QMessageBox.Information)
        box.setWindowTitle(title)
        box.setText(message)
        box.exec()
