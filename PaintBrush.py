from PySide2.QtGui import (QColor)
import numpy as np


class PaintBrush:
    def __init__(self, parent=None):
        self.RLData = [1, 1, 1, -1, -1, -1, -1, 1]
        self.Parent = parent
        self.mainapp = parent
        self.rl = self.mainapp.rl
        self.fl = self.mainapp.freqlist

        # To add an algorithm:
        # 1. Update numberAlgorithms below.
        # 2. Add in new algorithm function.
        # 3. Add in additional elif in the draw function.

        self.numberAlgorithms = 9
        self.currentAlgorithm = 1

    # Resets the links to the renderlist and frequency data in the main. S

    #def SetAlg9(self):
        #print("This is algorithm 9")
        #self.RLData.clear()
        #self.RLData = [1, 1, 1, -1, -1, -1, -1, 1]

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

    def makeTriangle(self, x1, y1, x2, y2, x3, y3, fill, col):
        newcol = QColor(col)
        return [4, x1, y1, x2, y2, x3, y3, fill, newcol]

    # Render function gateway.
    def draw(self, data, datapos, spectdata):
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
        elif self.currentAlgorithm == 9:
            self.algorithm9(data, spectdata)

    # Rendering Algorithms.

    def algorithm1(self, data):
        rx1 = np.random.random() * 2 - 1
        ry1 = np.random.random() * 2 - 1
        rx2 = np.random.random() * 2 - 1
        ry2 = np.random.random() * 2 - 1
        rx3 = np.random.random() * 2 - 1
        ry3 = np.random.random() * 2 - 1

        col = QColor()
        col.setRgbF(np.random.random(), np.random.random(), np.random.random(), 1)
        clear = QColor()
        clear.setRgbF(1, 1, 1, 1)
        self.rl.add(self.makeRectangle(-1, 1, 1, -1, True, clear))
        self.rl.add(self.makeTriangle(rx1, ry1, rx2, ry2, rx3, ry3, True, col))

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

    def algorithm9(self, data, spect):

        TriCol = QColor()
        Hue = data[0] * 10
        TriCol.setHsv(Hue, 255, 130, 255)

        print(spect)

        LineCol = QColor()
        LineCol.setHsv(Hue, 255, 200, 255)

        #WeightedFreqVal should be a value between 9 and 19 influenced by volume of sound coming in.
        WeightedFreqVal = 14.0

        Newx1 = (((WeightedFreqVal * self.RLData[0]) + self.RLData[6]) / (WeightedFreqVal + 1))
        Newy1 = (((WeightedFreqVal * self.RLData[1]) + self.RLData[7]) / (WeightedFreqVal + 1))
        Newx2 = (((WeightedFreqVal * self.RLData[2]) + self.RLData[0]) / (WeightedFreqVal + 1))
        Newy2 = (((WeightedFreqVal * self.RLData[3]) + self.RLData[1]) / (WeightedFreqVal + 1))
        Newx3 = (((WeightedFreqVal * self.RLData[4]) + self.RLData[2]) / (WeightedFreqVal + 1))
        Newy3 = (((WeightedFreqVal * self.RLData[5]) + self.RLData[3]) / (WeightedFreqVal + 1))
        Newx4 = (((WeightedFreqVal * self.RLData[6]) + self.RLData[4]) / (WeightedFreqVal + 1))
        Newy4 = (((WeightedFreqVal * self.RLData[7]) + self.RLData[5]) / (WeightedFreqVal + 1))

        self.rl.add(self.makeTriangle(self.RLData[0], self.RLData[1], Newx1, Newy1, Newx2, Newy2, True, TriCol))
        self.rl.add(self.makeTriangle(self.RLData[2], self.RLData[3], Newx2, Newy2, Newx3, Newy3, True, TriCol))
        self.rl.add(self.makeTriangle(self.RLData[4], self.RLData[5], Newx3, Newy3, Newx4, Newy4, True, TriCol))
        self.rl.add(self.makeTriangle(self.RLData[6], self.RLData[7], Newx4, Newy4, Newx1, Newy1, True, TriCol))

        self.rl.add(self.makeLine(self.RLData[0], self.RLData[1], self.RLData[2], self.RLData[3], LineCol))
        self.rl.add(self.makeLine(self.RLData[2], self.RLData[3], self.RLData[4], self.RLData[5], LineCol))
        self.rl.add(self.makeLine(self.RLData[4], self.RLData[5], self.RLData[6], self.RLData[7], LineCol))
        self.rl.add(self.makeLine(self.RLData[6], self.RLData[7], self.RLData[0], self.RLData[1], LineCol))

        self.RLData[0] = Newx1
        self.RLData[2] = Newx2
        self.RLData[4] = Newx3
        self.RLData[6] = Newx4
        self.RLData[1] = Newy1
        self.RLData[3] = Newy2
        self.RLData[5] = Newy3
        self.RLData[7] = Newy4
