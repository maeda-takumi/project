# app.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLockFile, QDir
from ui_main import MainWindow
from logic import AppLogic

def main():
    app = QApplication(sys.argv)

    lock_path = QDir.temp().filePath("trade_automation_app.lock")
    app_lock = QLockFile(lock_path)
    app_lock.setStaleLockTime(0)
    if not app_lock.tryLock(100):
        print("このアプリは既に起動しています。二重起動を防止するため終了します。")
        return
    # メインウィンドウ
    window = MainWindow()

    # ロジック接続
    logic = AppLogic(window, db_path="data/kabus_trade.db")
    logic.bind()
    app.aboutToQuit.connect(app_lock.unlock)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
