#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot


class SignalDB(QObject):
    
    desktopLRC_locked = Signal(bool)

    def __init__(self, parent=None):
        super(SignalDB, self).__init__(parent)


signalDB = SignalDB()


class LRCControlWidget(QFrame):

    """docstring for LRCControlWidget"""

    style = '''
        QFrame{
            border: None;
        }
    '''

    def __init__(self, parent=None):
        super(LRCControlWidget, self).__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_Hover, True)
        self.setWindowOpacity(0)

        self.lrcLabel = LRCLabel(self)

        self.setFixedSize(1200, 140)
        self.lrcLabel.setFixedSize(1000, 60)
        self.installEventFilter(self)

        self.moveCenter()
        self.lrcLabel.move(self.pos() + QPoint((self.width() - self.lrcLabel.width()) / 2, (self.height() - self.lrcLabel.height()) / 2))

    def moveCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverLeave:
            self.setWindowOpacity(0)
            return True
        else:
            return super(LRCControlWidget, self).eventFilter(obj, event)

    def mousePressEvent(self, event):
        self.setFocus()
        # 鼠标点击事件
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - \
                self.frameGeometry().topLeft()
            event.accept()

    def mouseReleaseEvent(self, event):
        # 鼠标释放事件
        if hasattr(self, "dragPosition"):
            del self.dragPosition

    def mouseMoveEvent(self, event):
        self.lrcLabel.move(self.pos() + QPoint((self.width() - self.lrcLabel.width()) / 2, (self.height() - self.lrcLabel.height()) / 2))
        self.setWindowOpacity(0.5)
        if hasattr(self, "dragPosition"):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.dragPosition)
                event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            signalDB.desktopLRC_locked.emit(not self.lrcLabel.isLocked())


class LRCLabel(QLabel):

    """docstring for LRCLabel"""

    def __init__(self, parent=None):
        super(LRCLabel, self).__init__(parent)
        self.parent = parent
        # FramelessWindowHint为无边界的窗口
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAlignment(Qt.AlignCenter)
        self.installEventFilter(self)

        self.initData()

        self.initFlags()
        self.initFont()
        self.initLinearGradient()
        self.initMaskLinearGradient()
        self.initTimer()

        self.initConnect()

        self.setText(self.tr("简易音乐播放器, dfdffd, 简易音乐播放器, dfdffd, 简易音乐播放器, dfdffd"))

    def initData(self):
        self.lrc_mask_width = 0
        self.lrc_mask_width_interval = 0

    def initFlags(self):
        self.locked = False

    def initFont(self):
        # 设置字体
        self.font = QFont()
        self.font.setFamily("Times New Roman")
        self.font.setBold(True)
        self.font.setPointSize(30)
        self.fontMetrics = QFontMetrics(self.font)

    def initLinearGradient(self):
        # 歌词的线性渐变填充
        self.linear_gradient = QLinearGradient()
        self.linear_gradient.setStart(0, 10)  # 填充的起点坐标
        self.linear_gradient.setFinalStop(0, 40)  # 填充的终点坐标
        # 第一个参数终点坐标，相对于我们上面的区域而言，按照比例进行计算
        self.linear_gradient.setColorAt(0.1, QColor(14, 179, 255))
        self.linear_gradient.setColorAt(0.5, QColor(114, 232, 255))
        self.linear_gradient.setColorAt(0.9, QColor(14, 179, 255))

    def initMaskLinearGradient(self):
        # 遮罩的线性渐变填充
        self.mask_linear_gradient = QLinearGradient()
        self.mask_linear_gradient.setStart(0, 10)
        self.mask_linear_gradient.setFinalStop(0, 40)
        self.mask_linear_gradient.setColorAt(0.1, QColor(222, 54, 4))
        self.mask_linear_gradient.setColorAt(0.5, QColor(255, 72, 16))
        self.mask_linear_gradient.setColorAt(0.9, QColor(222, 54, 4))

    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateLRC)

    def initConnect(self):
        signalDB.desktopLRC_locked.connect(self.setLocked)

    def isLocked(self):
        return self.locked

    @Slot(bool)
    def setLocked(self, flag):
        assert isinstance(flag, bool)
        self.locked = flag

    def setText(self, text):
        super(LRCLabel, self).setText(text)
        self.textWidth = self.fontMetrics.width(text)
        self.textHeight = self.fontMetrics.height()

    # 开启遮罩，需要指定当前歌词开始与结束之间的时间间隔
    def start_lrc_mask(self, intervaltime):
        # 这里设置每隔30毫秒更新一次遮罩的宽度，因为如果更新太频繁
        # 会增加CPU占用率，而如果时间间隔太大，则动画效果就不流畅了
        count = intervaltime / 30

        # 获取遮罩每次需要增加的宽度，这里的800是部件的固定宽度
        self.lrc_mask_width_interval = self.width() / count
        self.lrc_mask_width = 0
        self.timer.start(30)

    def stop_lrc_mask(self):
        self.timer.stop()
        self.lrc_mask_width = 0
        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            if self.locked:
                self.parent.setWindowOpacity(0)
                return super(LRCLabel, self).eventFilter(obj, event)
            else:
                self.parent.setWindowOpacity(0.5)
                return True
        else:
            return super(LRCLabel, self).eventFilter(obj, event)

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setFont(self.font)

        # 先绘制底层文字，作为阴影，这样会使显示效果更加清晰，且更有质感
        painter.setPen(QColor(0, 0, 0, 200))

        startY = (self.height() - self.font.pointSize()) / 2

        painter.drawText(
            1, 1, self.width(), self.height(), Qt.AlignCenter, self.text())  # 对齐

        # 再在上面绘制渐变文字
        painter.setPen(QPen(self.linear_gradient, 0))
        painter.drawText(
            0, 0, self.width(), self.height(), Qt.AlignCenter, self.text())

        # 设置歌词遮罩
        painter.setPen(QPen(self.mask_linear_gradient, 0))
        painter.drawText((self.width() - self.textWidth) / 2, (self.height() - self.textHeight) / 2,
                         self.lrc_mask_width, self.height(), Qt.AlignLeft, self.text())

    def updateLRC(self):
        # 每隔一段固定的时间笼罩的长度就增加一点
        self.lrc_mask_width += self.lrc_mask_width_interval
        self.update()  # 更新widget，但是并不立即重绘，而是安排一个Paint事件，当返回主循环时由系统来重绘

    def moveCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.setFocus()
        # 鼠标点击事件
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - \
                self.frameGeometry().topLeft()
            event.accept()

    def mouseReleaseEvent(self, event):
        # 鼠标释放事件
        if hasattr(self, "dragPosition"):
            del self.dragPosition

    def mouseMoveEvent(self, event):
        self.parent.move(self.pos() - QPoint((self.parent.width() - self.width()) / 2, (self.parent.height() - self.height()) / 2))
        if hasattr(self, "dragPosition"):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.dragPosition)
                event.accept()


class MainWindow(QMainWindow):
    """docstring for QMainWindow"""
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFixedSize(400, 200)
        self.button = QPushButton("LRC", self)
        self.button.clicked.connect(self.showLRC)

        self.lrc = LRCControlWidget(self)

        self.moveCenter()

    def showLRC(self):
        if self.lrc.lrcLabel.isVisible():
            self.lrc.hide()
            self.lrc.lrcLabel.hide()
            self.lrc.lrcLabel.stop_lrc_mask()
        else:
            self.lrc.show()
            self.lrc.lrcLabel.show()
            self.lrc.lrcLabel.start_lrc_mask(2000)

    def moveCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    exitCode = app.exec_()
    sys.exit(exitCode)
