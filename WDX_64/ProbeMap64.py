#!/usr/bin/env python2

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

import numpy as np

from CursorRect import CursorRect

from viridis import viridis as cmap

ACT_MAX = 300.
ACT_MIN = 0.

class ProbeMap64(QtGui.QLabel):

    dragAndDropAccepted = QtCore.pyqtSignal(int, int, int)

    def __init__(self, height, img):
        super(ProbeMap64, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.setStyleSheet("background-color: #000000")

        # load our background image
        self.pixmap = QtGui.QPixmap(img)

        # store original dimensions
        self._w = float(self.pixmap.size().width())
        self._h = float(self.pixmap.size().height())

        # set our widget size
        self.setFixedHeight(height)
        self.setFixedWidth(self.widthForHeight(height * 1.5))

        # scale pixmap to widget
        self.scaled_pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio,
                        transformMode=Qt.SmoothTransformation)

        # set widget aspect ratio
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                        QtGui.QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)

        # magic numbers, taken empirically from image for sake of this specific script
        self.x_offset = int(160 / self._w * self.scaled_pixmap.width())
        self.dx =       int(29 / self._w * self.scaled_pixmap.width())
        self.y_offset = int(107 / self._h * self.scaled_pixmap.height())
        self.dy =       int(28.5 / self._h * self.scaled_pixmap.height())
        self.widget_x_offset = (self.size().width() - self.scaled_pixmap.width()) / 2

        # initialize cursor at first index
        self.cursor = CursorRect(
                        self.size().width() / 2,
                        self.y_offset + 1.7 * self.dy,
                        int(self.size().width() * .9),
                        int(self.size().height() * .1),
                        1)
        self.index = (0, 0)

        # define probe pad geometery
        self.cols = 2
        self.rows = 32

        # create array of pad intensities
        self.activity = np.zeros((self.rows, self.cols))

        # create array of cursors to make glow
        self.pads = []

        # allocate positions
        for row in range(self.rows):
            for col in range(self.cols):
                self.pads.append(
                    CursorRect(
                        self.widget_x_offset + self.x_offset + self.dx * col,   # center x
                        self.y_offset + self.dy * row,                          # center y
                        5,                                                      # width
                        5,                                                      # height
                        1))                                                     # corner rounding

    def setActivity(self, activity):
        self.activity = activity
        self.repaint()

    def increment(self):
        if self.index[1] < 28:
            self.index = (0, self.index[1] + 1)
        self.set_index(*self.index)
        self.dragAndDropAccepted.emit(0, self.index[1], 0)

    def decrement(self):
        if self.index[1] > 0:
            self.index = (0, self.index[1] - 1)
        self.set_index(*self.index)
        self.dragAndDropAccepted.emit(0, self.index[1], 0)

    def set_position(self, x, y):
        x_index, y_index = self.position_to_index(x, y)

        # get array index from pixel position
        new_x, new_y = self.index_to_position(x_index, y_index)

        self.cursor.move(new_x, new_y)
        self.repaint()

        shank = x_index
        row = y_index
        col = 0
        self.dragAndDropAccepted.emit(shank, row, col)
        self.index = (x_index, y_index)

    def set_index(self, x, y):
        new_x, new_y = self.index_to_position(x, y)

        self.cursor.move(new_x, new_y)
        self.repaint()
        shank = 0
        row = y
        col = 0
        self.dragAndDropAccepted.emit(shank, row, col)
        self.index = (x, y)

    def position_to_index(self, pos_x, pos_y):
        x_index = 0

        y_index = ((pos_y + self.dy) - self.y_offset - self.cursor.h / 2) / self.dy
        if y_index < 0:
            y_index = 0
        if y_index > 28:
            y_index = 28

        return (x_index, y_index)

    def index_to_position(self, ind_x, ind_y):
        # get array index from pixel position
        new_x = self.size().width() / 2
        new_y = ((ind_y + 0.79) * self.dy) + self.y_offset #- self.cursor.h / 24 * self.dx) + self.x_offset + self.widget_x_offset

        # sanitize y position
        if new_y < (0 * self.dy) + self.y_offset:
            new_y = (0 * self.dy) + self.y_offset
        if new_y > (28 * self.dy) + self.y_offset:
            new_y = (28 * self.dy) + self.y_offset

        # correct for slight alignment error due to integer rounding
        if ind_x >= 2:
            offset = 1
        else:
            offset = 0

        return (new_x + offset, new_y + 6)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        pen = painter.pen()
        pen.setStyle(Qt.NoPen)
        painter.setPen(pen)

        # draw image centrally in the widget
        point = QtCore.QPoint(0,0)
        point.setX((self.size().width() - self.scaled_pixmap.width())/2)
        point.setY((self.size().height() - self.scaled_pixmap.height())/2)
        painter.drawPixmap(point, self.scaled_pixmap)

        for row in range(self.rows):
            for col in range(self.cols):
                brush = QtGui.QBrush(QtGui.QColor(*tuple(cmap(self.activity[row, col]))))
                painter.setBrush(brush)
                painter.drawRoundedRect(*self.pads[2 * row + col].params(), mode=Qt.RelativeSize)

        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 64))
        painter.setBrush(brush)
        pen = painter.pen()
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRoundedRect(*self.cursor.params(), mode=Qt.RelativeSize)

    def mousePressEvent(self, event):
        self.moved = False
        if event.button() == QtCore.Qt.LeftButton:
            # center the cursor on the mouse
            self.cursor.move(event.pos().x() , event.pos().y())

            self.moved = True
            self.repaint()

    def mouseMoveEvent(self, event):
        if self.moved:
            # center cursor
            self.cursor.move(event.pos().x(), event.pos().y())
            self.repaint()

    def mouseReleaseEvent(self, event):
        if self.moved:
            self.set_position(event.pos().x(), event.pos().y())
            self.moved = False

    def widthForHeight(self, height):
        return int((self._w / self._h) * height)


if __name__ =="__main__":
    import sys
    def printSelection(tup):
        print 'coords selected: ', tup

    app = QtGui.QApplication(sys.argv)
    probeMap = ProbeMap(300, 'shanks.jpg')
    probeMap.chanSelected.connect(printSelection)
    probeMap.show()
    sys.exit(app.exec_())