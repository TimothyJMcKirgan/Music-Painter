from PySide2.QtGui import (QColor)
import numpy as np


class PaintBrush:
    def __init__(self, parent=None):
        self.Parent = parent
        self.mainapp = parent
        self.rl = self.mainapp.rl
        self.fl = self.mainapp.freqlist

        # To add an algorithm:
        # 1. Update numberAlgorithms below.
        # 2. Add in new algorithm function.
        # 3. Add in additional elif in the draw function.

        self.numberAlgorithms = 8
        self.currentAlgorithm = 1

    # Resets the links to the renderlist and frequency data in the main. S
    def resetlistlinks(self):
        self.rl = self.mainapp.rl
        self.fl = self.mainapp.freqlist

    # Accessor functions for the render and frequency lists.
    def getRenderList(self, n):
        if n >= 0 and n < len(self.rl):
            return self.rl[n]
        else:
            return None

    def getFrequencyList(self, n):
        if n >= 0 and n < len(self.fl):
            return self.fl[n]
        else:
            return None

    def getLastRenderList(self, n):
        if n > 0 and n <= len(self.rl):
            return self.rl[len(self.rl) - n]
        else:
            return None

    def getLastFrequencyList(self, n):
        if n > 0 and n <= len(self.fl):
            return self.fl[len(self.fl) - n]
        else:
            return None

    # Object creation for adding to the renderlist.
    #  0 = point, 1 = line, 2 = circle, 3 = rectangle
    def makePoint(self, x, y, col):
        newcol = QColor(col)
        return [0, x, y, newcol]

    def makeLine(self, x1, y1, x2, y2, col):
        newcol = QColor(col)
        return [1, x1, y1, x2, y2, newcol]

    def makeCircle(self, cx, cy, rad, fill, col):
        newcol = QColor(col)
        return [2, cx, cy, rad, fill, newcol]

    def makeRectangle(self, ULx, ULy, LRx, LRy, fill, col):
        newcol = QColor(col)
        return [3, ULx, ULy, LRx, LRy, fill, newcol]

    # Render function gateway.
    def draw(self, data, datapos):
        if self.currentAlgorithm == 1:
            self.algorithm1(data)
        elif self.currentAlgorithm == 2:
            self.algorithm2(data)
        elif self.currentAlgorithm == 3:
            self.algorithm3(data, datapos)
        elif self.currentAlgorithm == 4:
            self.algorithm4(data, datapos)
        elif self.currentAlgorithm == 5:
            self.algorithm5(data, datapos)
        elif self.currentAlgorithm == 6:
            self.algorithm6(data, datapos)
        elif self.currentAlgorithm == 7:
            self.algorithm7(data, datapos)
        elif self.currentAlgorithm == 8:
            self.algorithm8(data, datapos)

    # Rendering Algorithms.

    def algorithm1(self, data):
        rx = np.random.random() * 2 - 1
        ry = np.random.random() * 2 - 1

        col = QColor()
        col.setRgbF(np.random.random(), np.random.random(), np.random.random(), 1)
        self.rl.add(self.makePoint(rx, ry, col))

    def algorithm2(self, data):
        rtheta = np.random.random() * 2 * np.pi
        rx = np.cos(rtheta)
        ry = np.sin(rtheta)

        col = QColor()
        col.setRgbF(np.random.random(), np.random.random(), np.random.random(), 1)
        self.rl.add(self.makePoint(rx, ry, col))

    def algorithm3(self, data, pos):
        numfreq = len(self.fl)
        maxfreq = 5000
        x = 2 * pos / numfreq - 1
        y = data[0] / maxfreq

        col = QColor()
        col.setRgbF(1, 0, 0, 1)
        self.rl.add(self.makeLine(x, 0.25, x, y + .25, col))

        if len(data) > 1:
            y = data[1] / maxfreq
            col.setRgbF(0, 1, 0, 1)
            self.rl.add(self.makeLine(x, -.75, x, y - .75, col))

    def algorithm4(self, data, pos):
        numfreq = len(self.fl)
        maxfreq = 5000
        x = 2 * pos / numfreq - 1
        y = data[0] / maxfreq

        col = QColor()
        col.setRgbF(1, 0, 0, 1)
        self.rl.add(self.makePoint(x, y, col))

        if len(data) > 1:
            y = data[1] / maxfreq
            col.setRgbF(0, .5, 0, 1)
            self.rl.add(self.makePoint(x, y, col))

    def algorithm5(self, data, pos):
        numfreq = len(self.fl)
        maxfreq = 5000
        x = 2 * pos / numfreq - 1
        y = data[0] / maxfreq

        col = QColor()
        col.setRgbF(0.5, 0.3, 0.7, 1)
        self.rl.add(self.makePoint(x, y, col))

        if len(data) > 1:
            y = data[1] / maxfreq
            col.setRgbF(1, .7, 0, 0.5)
            self.rl.add(self.makePoint(x, y, col))

    def algorithm6(self, data, pos):
        numfreq = len(self.fl)
        maxfreq = 2000
        x = 2 * pos / numfreq - 1
        y = data[0] / maxfreq * 2

        col = QColor()
        col.setRgbF(1, 0, 0, 1)
        y = (sum(data) / len(data)) / maxfreq

        self.rl.add(self.makeLine(x, -.5, x, y - .5, col))

    def algorithm7(self, data, pos):
        numfreq = len(self.fl)
        maxfreq = 2000
        x = 2 * pos / numfreq - 1
        y = data[0] / maxfreq * 2

        col = QColor()
        col.setRgbF(1, 0, 0, 1)
        y = (sum(data) / len(data)) / maxfreq

        self.rl.add(self.makeRectangle(x, y, x+0.01, y-0.01, True, col))

    def algorithm8(self, data, pos):
        numfreq = len(self.fl)
        maxfreq = 2000
        x = 2 * pos / numfreq - 1
        y = data[0] / maxfreq * 2

        col = QColor()
        col.setRgbF(1, 0, 0, 1)
        y = (sum(data) / len(data)) / maxfreq

        self.rl.add(self.makeCircle(x, y-0.5, 0.01, True, col))

        # col.setRgbF(0, 1, 1, 1)
        # rct = self.makeRectangle(.5, .5, 0, 0, True, col)
        # self.rl.add(rct)
        #
        # col.setRgbF(0, 0, 0, 1)
        # rct = self.makeRectangle(.5, .5, 0, 0, False, col)
        # self.rl.add(rct)
        #
        # col.setRgbF(1, 0, 1, 1)
        # line = self.makeLine(-1, -.5, 0, 0.5, col)
        # self.rl.add(line)
        #
        # # col.setRgbF(1,1, 0, 1)
        # # cricle = self.makeCircle(-.5, -.5, 0.5, False, col)
        # # self.rl.add(cricle)
        #
        # col.setRgbF(1, 0, 0, 1)
        # cricle = self.makeCircle(-.5, -.5, 0.2, True, col)
        # self.rl.add(cricle)
        #
        # col.setRgbF(1,1, 0, 1)
        # cricle = self.makeCircle(-.5, -.5, 0.5, False, col)
        # self.rl.add(cricle)

    #####################################################
    # Code used during testing but shows structure.
    #####################################################

    # print(data)

    # rx = np.random.random() * 2 - 1
    # ry = np.random.random() * 2 - 1
    #
    # col = QColor()
    # col.setRgbF(np.random.random(), np.random.random(), np.random.random(), 1)
    # self.rl.add(self.makePoint(rx, ry, col))

    # self.rl.add(self.makePoint(1, 1, col))
    # self.rl.add(self.makePoint(-0.75, -0.75, col))
    # self.rl.add(self.makePoint(0, 1 / 2, col))
    #
    # for i in range(360):
    #     self.rl.add(self.makePoint(0.75 * np.cos(np.pi / 180 * i), 0.75 * np.sin(np.pi / 180 * i), col))
    #
    # col.setRgbF(0, 1, 1, 1)
    # rct = self.makeRectangle(.5, .5, 0, 0, True, col)
    # self.rl.add(rct)
    #
    # col.setRgbF(0, 0, 0, 1)
    # rct = self.makeRectangle(.5, .5, 0, 0, False, col)
    # self.rl.add(rct)
    #
    # col.setRgbF(1, 0, 1, 1)
    # line = self.makeLine(-1, -.5, 0, 0.5, col)
    # self.rl.add(line)
    #
    # # col.setRgbF(1,1, 0, 1)
    # # cricle = self.makeCircle(-.5, -.5, 0.5, False, col)
    # # self.rl.add(cricle)
    #
    # col.setRgbF(1, 0, 0, 1)
    # cricle = self.makeCircle(-.5, -.5, 0.2, True, col)
    # self.rl.add(cricle)
    #
    # col.setRgbF(1,1, 0, 1)
    # cricle = self.makeCircle(-.5, -.5, 0.5, False, col)
    # self.rl.add(cricle)
