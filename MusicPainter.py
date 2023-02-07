#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 10/1/2022
Revised: 10/16/2022

@authors: Luke Zolenski & Don Spickler

This program is a music/sound visualizer for frequency data from either a wav file or
an input stream from a microphone.  It allows the user to set chunk size and rendering algorithm
and render images based on the wav or stream data.  It also has features to render as the
wav file is playing and to save the streamed music to a wav file.

"""

# System imports.
import platform
import sys
import os
import numpy as np
import wave
from scipy.io import wavfile
from threading import Thread
import sounddevice as sd
import pyaudio
import time
from PySide2.QtCore import (Qt, QSize, QDir, QPoint, QMarginsF, QRect, QLine)
from PySide2.QtGui import (QIcon, QFont, QCursor, QPainter, QColor, QFontMetrics,
                           QMouseEvent, QPageSize, QPageLayout, QPixmap, QBrush)
from PySide2.QtWidgets import (QApplication, QMainWindow, QStatusBar,
                               QToolBar, QDockWidget, QSpinBox, QHBoxLayout,
                               QVBoxLayout, QWidget, QLabel, QScrollArea, QMessageBox,
                               QInputDialog, QFileDialog, QDialog, QAction, QListWidget,
                               QTreeWidget, QSplitter, QAbstractItemView, QTreeWidgetItem,
                               QColorDialog, QFontDialog, QLineEdit, QFrame, QCheckBox,
                               QDialogButtonBox, QComboBox, QDoubleSpinBox, QHeaderView,
                               QTextEdit, QMenu, QStyleFactory)
from PySide2.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)

# Program imports of our modules.
from PaintBrush import PaintBrush

# For the Mac OS
os.environ['QT_MAC_WANTS_LAYER'] = '1'


class appcss:
    """
    Stylesheet for the program.
    """

    def __init__(self):
        super().__init__()
        self.css = """
            QMenu::separator { 
                background-color: #BBBBBB; 
                height: 1px; 
                margin: 3px 5px 3px 5px;
            }

        """

    def getCSS(self):
        return self.css


class ObjectListViewer(QWidget):
    """
    This is the control for the rendered image.  It takes the geometric data stored in
    the render list produced in the rendering algorithms and plots it. The default
    window is [-1,1] with aspect ratio expansion in one direction.  The control
    also has features for zooming and translation.
    """

    def __init__(self, parent=None, ma=None):
        super(ObjectListViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

        self.screen = [-1, 1, -1, 1]
        self.lastRenderListSize = 0
        self.renderAll = True
        self.zoomfactor = 1
        self.center = [0, 0]

        self.mousePosition = [0, 0]
        self.mouseDown = False
        self.setMouseTracking(True)

    def resetCenter(self):
        """
        Resets center to the origin.
        """
        self.center = [0, 0]
        self.repaint()

    def resetZoom(self):
        """
        Resets the zoom factor to 1.
        """
        self.zoomfactor = 1
        self.repaint()

    def resetCenterAndZoom(self):
        """
        Resets the center to the origin and zoom factor to 1.
        """
        self.center = [0, 0]
        self.zoomfactor = 1
        self.repaint()

    def mousePressEvent(self, e):
        """
        On a mouse down event on the left button, track its state.
        """
        self.mousePosition = QPoint(e.x(), e.y())
        if e.button() == Qt.LeftButton:
            self.mouseDown = True

    def wheelEvent(self, e) -> None:
        """
        On a mouse wheel event update the zoom factor.
        """
        self.zoomfactor *= (1 + e.delta() / 5000)
        if self.zoomfactor < 1:
            self.zoomfactor = 1
        if self.zoomfactor > 1000:
            self.zoomfactor = 1000
        self.repaint()

    def mouseReleaseEvent(self, e):
        """
        On a mouse up event track its state.
        """
        self.mouseDown = False

    def mouseMoveEvent(self, e):
        """
        On a mouse move event update the zoom factor if the control key is down
        and translate if the control key is not down.
        """
        lastmouseposition = self.mousePosition
        self.mousePosition = QPoint(e.x(), e.y())

        if self.mouseDown:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                pixmove = (self.mousePosition.x() - lastmouseposition.x()) + (
                        self.mousePosition.y() - lastmouseposition.y())
                self.zoomfactor *= (1 + pixmove / 100)
                if self.zoomfactor < 1:
                    self.zoomfactor = 1
                if self.zoomfactor > 1000:
                    self.zoomfactor = 1000
                self.repaint()
            else:
                xr = self.screen[1] - self.screen[0]
                yr = self.screen[3] - self.screen[2]
                self.center[0] += (self.mousePosition.x() - lastmouseposition.x()) * xr / self.width()
                self.center[1] += (self.mousePosition.y() - lastmouseposition.y()) * yr / self.height()
                self.repaint()

    def XYtoQPoint(self, x, y):
        """
        Covert real coordinates to screen coordinates.
        """
        xr = self.screen[1] - self.screen[0]
        yr = self.screen[3] - self.screen[2]
        # ptx = x / xr * self.width() + self.width() / 2
        # pty = -y / yr * self.height() + self.height() / 2
        ptx = (x + self.center[0]) / xr * self.width() + self.width() / 2
        pty = (self.center[1] - y) / yr * self.height() + self.height() / 2
        return QPoint(ptx, pty)

    def updateScreenBounds(self):
        """
        Update the screen bounds based on the center and zoom factor being used.
        """
        fullscreen = [-1, 1, -1, 1]
        ww = self.width()
        wh = self.height()
        if ww >= wh:
            fullscreen = [-ww / wh, ww / wh, -1, 1]
        else:
            fullscreen = [-1, 1, -wh / ww, wh / ww]
        for i in range(4):
            fullscreen[i] = fullscreen[i] * (1 / self.zoomfactor)
        self.screen[0] = self.center[0] - fullscreen[1]
        self.screen[1] = self.center[0] + fullscreen[1]
        self.screen[2] = self.center[1] - fullscreen[3]
        self.screen[3] = self.center[1] + fullscreen[3]

    def RenderPoint(self, qp, obj):
        """
        Draw a point to the screen.
        """
        qp.setPen(obj[3])
        qp.drawPoint(self.XYtoQPoint(obj[1], obj[2]))

    def RenderLine(self, qp, obj):
        """
        Draw a line to the screen.
        """
        qp.setPen(obj[5])
        pt1 = self.XYtoQPoint(obj[1], obj[2])
        pt2 = self.XYtoQPoint(obj[3], obj[4])
        line = QLine(pt1, pt2)
        qp.drawLine(line)

    def RenderCircle(self, qp, obj):
        """
        Draw a circle to the screen.
        """
        qp.setPen(obj[5])
        ulpt = self.XYtoQPoint(obj[1] - obj[3], obj[2] + obj[3])
        lrpt = self.XYtoQPoint(obj[1] + obj[3], obj[2] - obj[3])
        # rect = QRect(ulpt.x(), ulpt.y(), lrpt.x() - ulpt.x(), lrpt.y() - ulpt.y())
        rect = QRect(ulpt, lrpt)
        if obj[4]:
            qp.setBrush(obj[5])
            qp.drawEllipse(rect)
            qp.setBrush(QColor(0, 0, 0, 0))
        else:
            qp.drawEllipse(rect)

    def RendeRectangle(self, qp, obj):
        """
        Draw a rectangle to the screen.
        """
        qp.setPen(obj[6])
        ulpt = self.XYtoQPoint(obj[1], obj[2])
        lrpt = self.XYtoQPoint(obj[3], obj[4])
        # rect = QRect(ulpt.x(), ulpt.y(), lrpt.x() - ulpt.x(), lrpt.y() - ulpt.y())
        rect = QRect(ulpt, lrpt)
        if obj[5]:
            qp.fillRect(rect, obj[6])
        else:
            qp.drawRect(rect)

    def paintEvent(self, event):
        """
        Paint event override, clears the screen, loops through the render list of
        objects, and draws a border around the image.
        """
        self.updateScreenBounds()
        rl = self.mainapp.rl

        qp = QPainter()
        qp.begin(self)

        renderstart = 0
        if self.renderAll:
            # Clear Screen
            backgroundcolor = QColor()
            backgroundcolor.setRgbF(1, 1, 1, 1)
            qp.fillRect(0, 0, self.width(), self.height(), backgroundcolor)
        else:
            renderstart = self.lastRendetListSize

        for i in range(renderstart, rl.length()):
            obj = rl.get(i)
            if obj[0] == 0:
                self.RenderPoint(qp, obj)
            elif obj[0] == 1:
                self.RenderLine(qp, obj)
            elif obj[0] == 2:
                self.RenderCircle(qp, obj)
            elif obj[0] == 3:
                self.RendeRectangle(qp, obj)

        outline = QColor()
        outline.setRgb(0, 0, 0, 255)
        qp.setPen(outline)
        qp.drawRect(0, 0, self.width() - 1, self.height() - 1)
        qp.end()
        self.lastRenderListSize = rl.length()


class RenderList:
    """
    Convenience class for storing a list of items to be rendered.
    """
    def __init__(self):
        self.renderlist = []

    def add(self, item):
        self.renderlist.append(item)

    def clear(self):
        self.renderlist = []

    def length(self):
        return len(self.renderlist)

    def get(self, i):
        if i < 0 or i >= len(self.renderlist):
            return None
        return self.renderlist[i]


class MusicPainter(QMainWindow):
    """
    Main program application window.
    """

    def __init__(self, parent=None):
        super().__init__()
        self.Parent = parent
        self.mainapp = self

        # About information for the app.
        self.authors = "Luke Zolenski & Don Spickler"
        self.version = "1.1.1"
        self.program_title = "Music Painter"
        self.copyright = "2022"

        # Set GUI style
        self.Platform = platform.system()
        styles = QStyleFactory.keys()
        if "Fusion" in styles:
            app.setStyle('Fusion')

        # Set recording constants
        self.RECORDFORMAT = pyaudio.paInt16
        self.RECORDCHANNELS = 2
        self.RECORDRATE = 44100
        self.fullrecording = None

        # Setup Global Objects
        self.freqlist = None
        self.clipboard = QApplication.clipboard()
        self.rl = RenderList()
        self.paintbrush = PaintBrush(self)
        self.loadedFilename = ""
        self.titleoverridetext = ""
        self.music_thread = None
        self.playsoundstop = False
        self.initializeUI()

    # Adjoin a relative path for icons and help system.
    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    # Updates the title bar to contain the loaded file path or test.
    def updateProgramWindowTitle(self):
        title = self.program_title
        if self.titleoverridetext != "":
            title = title + " - " + self.titleoverridetext
        elif self.loadedFilename != "":
            title = title + " - " + self.loadedFilename
        self.setWindowTitle(title)

    # Initialize the window, calls create methods to set up the GUI.
    def initializeUI(self):
        self.setMinimumSize(800, 600)
        self.updateProgramWindowTitle()
        icon = QIcon(self.resource_path("icons/ProgramIcon.png"))
        self.setWindowIcon(icon)

        self.algorithmNum = QComboBox()
        for i in range(self.paintbrush.numberAlgorithms):
            self.algorithmNum.addItem(str(i + 1))

        self.ChunkSizesList = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
        self.chunkSize = QComboBox()
        for val in self.ChunkSizesList:
            self.chunkSize.addItem(str(val))
        self.chunkSize.setCurrentIndex(4)

        self.canvas = ObjectListViewer(self, self)

        self.createMenu()
        self.createToolBar()

        # self.statusBar = QStatusBar()
        # self.setStatusBar(self.statusBar)

        self.setCentralWidget(self.canvas)
        self.show()

    # Setup all menu and toolbar actions as well as create the menu.
    def createMenu(self):
        self.file_open_act = QAction(QIcon(self.resource_path('icons/FileOpen.png')), "&Open Wav File...", self)
        self.file_open_act.setShortcut('Ctrl+O')
        self.file_open_act.triggered.connect(self.openFile)
        self.file_open_act.setStatusTip("Open a wav file for rendering.")

        self.printImage_act = QAction(QIcon(self.resource_path('icons/print.png')), "&Print...", self)
        self.printImage_act.setShortcut('Ctrl+P')
        self.printImage_act.triggered.connect(self.printImage)
        self.printImage_act.setStatusTip("Print the image.")

        self.printPreviewImage_act = QAction(QIcon(self.resource_path('icons/preview.png')), "Print Pre&view...", self)
        self.printPreviewImage_act.triggered.connect(self.printPreviewImage)
        self.printPreviewImage_act.setStatusTip("Print preview the image.")

        quit_act = QAction("E&xit", self)
        quit_act.triggered.connect(self.close)
        quit_act.setStatusTip("Shut down the application.")

        self.copyImage_act = QAction(QIcon(self.resource_path('icons/CopyImage.png')), "Copy &Image", self)
        self.copyImage_act.setShortcut('Ctrl+C')
        self.copyImage_act.triggered.connect(self.copyImageToClipboard)
        self.copyImage_act.setStatusTip("Copy the image to the clipboard.")

        self.saveImage_act = QAction(QIcon(self.resource_path('icons/CopyImage2.png')), "Save Image &As...", self)
        self.saveImage_act.triggered.connect(self.saveAsImage)
        self.saveImage_act.setStatusTip("Save the image.")

        self.render_act = QAction(QIcon(self.resource_path('icons/Next.png')), "&Render", self)
        self.render_act.triggered.connect(self.renderImage)
        self.render_act.setStatusTip("Render the image.")

        self.clear_act = QAction("&Clear Image", self)
        self.clear_act.triggered.connect(self.clearImage)
        self.clear_act.setStatusTip("Clear the image.")

        self.resetCenter_act = QAction("Reset Center", self)
        self.resetCenter_act.triggered.connect(self.canvas.resetCenter)
        self.resetCenter_act.setStatusTip("Reset the center to the origin.")

        self.resetZoom_act = QAction("Reset Zoom", self)
        self.resetZoom_act.triggered.connect(self.canvas.resetZoom)
        self.resetZoom_act.setStatusTip("Reset the zoom factor to 1.")

        self.resetCenterZoom_act = QAction("Reset Center and Zoom", self)
        self.resetCenterZoom_act.triggered.connect(self.canvas.resetCenterAndZoom)
        self.resetCenterZoom_act.setStatusTip("Reset the center to the origin and zoom factor to 1.")

        self.properties_act = QAction("File &Information...", self)
        self.properties_act.triggered.connect(self.SoundDataProperties)
        self.properties_act.setStatusTip("View the wav file information.")

        self.play_act = QAction(QIcon(self.resource_path('icons/Play.png')), "Render and &Play", self)
        self.play_act.triggered.connect(self.PlaySoundData)
        self.play_act.setStatusTip("Render the image while playing the wav file.")

        self.stop_act = QAction(QIcon(self.resource_path('icons/Stop.png')), "&Stop Render", self)
        self.stop_act.triggered.connect(self.StopSoundData)
        self.stop_act.setStatusTip("Stop the rendering of the image.")

        self.record_act = QAction(QIcon(self.resource_path('icons/Record.png')), "&Record", self)
        self.record_act.triggered.connect(self.RecordSoundData)
        self.record_act.setStatusTip("Record sound and render image.")

        self.saverecording_act = QAction(QIcon(self.resource_path('icons/FileSave.png')), "&Save Recording", self)
        self.saverecording_act.triggered.connect(self.SaveRecording)
        self.saverecording_act.setStatusTip("Save recorded sound to wav file.")

        self.stoprecord_act = QAction(QIcon(self.resource_path('icons/Stop.png')), "&Stop Recording", self)
        self.stoprecord_act.triggered.connect(self.StopRecordData)
        self.stoprecord_act.setStatusTip("Stop recording.")

        selectTheme_act = QAction("&Theme...", self)
        selectTheme_act.triggered.connect(self.SelectTheme)

        # Create help menu actions
        self.help_about_act = QAction(QIcon(self.resource_path('icons/About.png')), "&About...", self)
        self.help_about_act.triggered.connect(self.aboutDialog)
        self.help_about_act.setStatusTip("Information about the program.")

        # Create the menu bar
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.file_open_act)
        file_menu.addAction(self.properties_act)
        file_menu.addAction(self.render_act)
        file_menu.addAction(self.play_act)
        file_menu.addAction(self.stop_act)
        file_menu.addSeparator()
        file_menu.addAction(quit_act)

        record_menu = menu_bar.addMenu('&Record')
        record_menu.addAction(self.record_act)
        record_menu.addAction(self.stoprecord_act)
        record_menu.addAction(self.saverecording_act)

        image_menu = menu_bar.addMenu('&Image')
        image_menu.addAction(self.copyImage_act)
        image_menu.addAction(self.saveImage_act)
        image_menu.addSeparator()
        image_menu.addAction(self.printImage_act)
        image_menu.addAction(self.printPreviewImage_act)
        image_menu.addSeparator()
        image_menu.addAction(self.resetCenter_act)
        image_menu.addAction(self.resetZoom_act)
        image_menu.addAction(self.resetCenterZoom_act)
        image_menu.addSeparator()
        image_menu.addAction(self.clear_act)

        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction(self.help_about_act)

    # Set up toolbar
    def createToolBar(self):
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(20, 20))
        self.addToolBar(tool_bar)

        tool_bar.addAction(self.file_open_act)
        tool_bar.addAction(self.render_act)
        tool_bar.addAction(self.play_act)
        tool_bar.addAction(self.stop_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.record_act)
        tool_bar.addAction(self.stoprecord_act)
        tool_bar.addAction(self.saverecording_act)

        tool_bar.addSeparator()
        tool_bar.addAction(self.copyImage_act)
        tool_bar.addAction(self.saveImage_act)
        tool_bar.addAction(self.printImage_act)
        tool_bar.addAction(self.printPreviewImage_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.help_about_act)
        tool_bar.addSeparator()

        tool_bar.addWidget(QLabel("   Algorithm: "))
        tool_bar.addWidget(self.algorithmNum)

        tool_bar.addWidget(QLabel("   Chunk Size: "))
        tool_bar.addWidget(self.chunkSize)

    # Display information about program dialog box.
    def aboutDialog(self):
        QMessageBox.about(self, self.program_title + "  Version " + self.version,
                          self.authors + "\nVersion " + self.version +
                          "\nCopyright " + self.copyright +
                          "\nDeveloped in Python using the \nPySide, SciPy, and PyAudio toolsets.")

    # def setStatusText(self, text):
    #     self.statusBar.showMessage(text)

    # Theme setter, not currently being used in the program.
    def SelectTheme(self):
        items = QStyleFactory.keys()
        if len(items) <= 1:
            return

        items.sort()
        item, ok = QInputDialog.getItem(self, "Select Theme", "Available Themes", items, 0, False)

        if ok:
            self.Parent.setStyle(item)

    # Uses NumPy fft to compute frequency spectrum.
    def getSpectrum(self, data, samplingfreq):
        spectrum = np.abs(np.fft.rfft(data))
        freq = np.fft.rfftfreq(data.size, d=1.0 / samplingfreq)
        return spectrum, freq

    # Returns the dominate frequency from a spectrum and frequency list.
    def getMaxFreq(self, spec, freq):
        if len(spec) == 0 or len(freq) == 0:
            return 0

        maxfreq = freq[0]
        maxspec = spec[0]
        for j in range(len(spec)):
            if spec[j] > maxspec:
                maxspec = spec[j]
                maxfreq = freq[j]

        return maxfreq

    # Executed in a separate thread.  Reads in the wav file, precomputes the frequencies
    # for the entire file, depending on the mode will either render the data all at once
    # with the current algorithm and chunk size or it will render while the file is being
    # played.
    def dotheplay(self, playmusic):
        chunk = self.ChunkSizesList[self.chunkSize.currentIndex()]
        self.paintbrush.currentAlgorithm = self.algorithmNum.currentIndex() + 1

        samplingfreq, sound = wavfile.read(self.loadedFilename)
        channels = sound.shape[1]
        samples = sound.shape[0]

        channelData = []
        for i in range(channels):
            channelData.append(sound[:, i])

        channelChunks = []
        for i in range(channels):
            soundslices = []
            start = 0
            while start + chunk <= samples:
                soundslices.append(channelData[i][start:start + chunk])
                start += chunk
            channelChunks.append(soundslices)

        af = wave.open(self.loadedFilename, 'rb')
        pa = pyaudio.PyAudio()
        # wavframerate = af.getframerate()
        stream = pa.open(format=pa.get_format_from_width(af.getsampwidth()),
                         channels=af.getnchannels(),
                         rate=af.getframerate(),
                         output=True)

        self.freqlist = []
        freqcap = 8500

        # precompute the frequency data.
        for i in range(len(channelChunks[0])):
            channelFreqs = []
            for k in range(channels):
                spect, freq = self.getSpectrum(channelChunks[k][i], samplingfreq)
                maxfreq = self.getMaxFreq(spect, freq)
                channelFreqs.append(maxfreq)

            maxfreqch = max(channelFreqs)
            if maxfreqch > freqcap:
                channelFreqs = [0, 0]
            self.freqlist.append(channelFreqs)
            # self.setStatusText("Processing segment "+ str(i+1) + " of " + str(len(channelChunks[0])))

        rd_data = []
        if playmusic:
            af.rewind()
            rd_data = af.readframes(chunk)

        self.paintbrush.resetlistlinks()

        i = 0
        while i < len(self.freqlist) and (not self.playsoundstop):
            if i < len(self.freqlist):
                self.paintbrush.draw(self.freqlist[i], i)
                self.canvas.renderAll = False
                self.canvas.update()
                self.canvas.renderAll = True

            if playmusic:
                stream.write(rd_data)
                rd_data = af.readframes(chunk)
            #     self.setStatusText("")
            # else:
            #     self.setStatusText("")
            # eltime = "%.3f" %  (i * chunk / wavframerate)
            # self.setStatusText(eltime + " sec.")

            i += 1

        stream.stop_stream()
        stream.close()
        af.close()
        pa.terminate()
        # self.setStatusText("")
        # Remove Thread
        self.music_thread = None
        self.canvas.update()

        # self.play_act.setEnabled(True)

    # Checks id the file is readable with both scipy and pyaudio
    def checkFile(self):
        if self.loadedFilename == '':
            QMessageBox.warning(self, "File Not Opened", "A Wav file needs to opened before rendering.",
                                QMessageBox.Ok)
            return False

        try:
            samplingfreq, sound = wavfile.read(self.loadedFilename)
            af = wave.open(self.loadedFilename, 'rb')
            af.close
        except:
            QMessageBox.warning(self, "File Could Not be Loaded",
                                "The file " + self.loadedFilename + " could not be loaded.",
                                QMessageBox.Ok)
            return False

        return True

    # Sets the rendering thread to render the entire wav file immediately.
    def renderImage(self):
        if not self.checkFile():
            return

        if not self.music_thread:
            self.music_thread = Thread(target=self.dotheplay, args=(False,), daemon=True)
            self.clearImage()

        if self.music_thread.is_alive():
            return

        self.playsoundstop = False
        self.music_thread.start()

    # Sets the rendering and playing thread to play while rendering.
    def PlaySoundData(self):
        if not self.checkFile():
            return

        if not self.music_thread:
            self.music_thread = Thread(target=self.dotheplay, args=(True,), daemon=True)
            self.clearImage()

        if self.music_thread.is_alive():
            return

        self.playsoundstop = False
        self.music_thread.start()

    # Stops the playing and rendering of the wav file.
    def StopSoundData(self):
        self.playsoundstop = True
        self.music_thread = None
        self.titleoverridetext = ""
        self.updateProgramWindowTitle()

    # Executed in a separate thread.  This will use the current chunk size and algorithm
    # to stream data from the microphone through the numpy fft to the rendering algorithms.
    # At the end it will join the frames into a single data file that can be saved to a
    # wav file.
    def dotherecord(self):
        chunk = self.ChunkSizesList[self.chunkSize.currentIndex()]
        self.paintbrush.currentAlgorithm = self.algorithmNum.currentIndex() + 1

        p = pyaudio.PyAudio()
        stream = p.open(format=self.RECORDFORMAT,
                        channels=self.RECORDCHANNELS,
                        rate=self.RECORDRATE,
                        input=True,
                        frames_per_buffer=chunk)

        frames = []
        self.freqlist = []
        freqcap = 8500
        self.paintbrush.resetlistlinks()

        while not self.playsoundstop:
            data = stream.read(chunk)
            numpydata = np.frombuffer(data, dtype=np.int16)
            # frame = np.stack((numpydata[::2], numpydata[1::2]), axis=0)
            # frame = []
            # for i in range(self.RECORDCHANNELS):
            #     frame.append(numpydata[i::2])

            channelFreqs = []
            for i in range(self.RECORDCHANNELS):
                # channelData.append(numpydata[:, i])
                # spect, freq = self.getSpectrum(frame[i], self.RECORDRATE)
                spect, freq = self.getSpectrum(numpydata[i::self.RECORDCHANNELS], self.RECORDRATE)
                maxfreq = self.getMaxFreq(spect, freq)
                channelFreqs.append(maxfreq)

            maxfreqch = max(channelFreqs)
            if maxfreqch > freqcap:
                channelFreqs = [0, 0]
            self.freqlist.append(channelFreqs)

            if channelFreqs != [0, 0]:
                pos = len(self.freqlist) - 1
                self.paintbrush.draw(self.freqlist[pos], pos)
                self.canvas.renderAll = False
                self.canvas.update()
                self.canvas.renderAll = True

            # print(channelFreqs)

            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        self.fullrecording = b''.join(frames)
        self.music_thread = None

    # Sets up the thread to record the sound data from the microphone.
    def RecordSoundData(self):
        if not self.music_thread:
            self.music_thread = Thread(target=self.dotherecord, daemon=True)
            self.clearImage()

        if self.music_thread.is_alive():
            return

        self.playsoundstop = False
        self.titleoverridetext = "Recording"
        self.updateProgramWindowTitle()
        self.music_thread.start()
        # self.titleoverridetext = ""
        # self.updateProgramWindowTitle()

    # Stops the recording.
    def StopRecordData(self):
        self.playsoundstop = True
        self.music_thread = None
        self.titleoverridetext = ""
        self.updateProgramWindowTitle()

    # Saves the current recorded data to a wav file.
    def SaveRecording(self):
        if self.fullrecording is None:
            return

        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('wav')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['Wav Files (*.wav)'])
        dialog.setWindowTitle('Save As')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                wf = wave.open(file_name, "wb")
                wf.setnchannels(self.RECORDCHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.RECORDFORMAT))
                wf.setframerate(self.RECORDRATE)
                wf.writeframes(self.fullrecording)
                wf.close()

    # Reports the properties of the currently loaded wav file.
    def SoundDataProperties(self):
        try:
            af = wave.open(self.loadedFilename, 'rb')
            samplingfreq = af.getframerate()
            channels = af.getnchannels()
            samples = af.getnframes()
            musictime = samples / samplingfreq
            af.close()

            timesec = "%.3f" % musictime
            timemin = musictime // 60
            timeminsec = "%.3f" % (musictime - timemin * 60)

            reportstring = "Sampling Frequency: " + str(samplingfreq) + "\n"
            reportstring += "Number of Samples: " + str(samples) + "\n"
            reportstring += "Length: " + timesec + " sec. = " + str(int(timemin)) + " min. " + timeminsec + " sec.\n"
            reportstring += "Number of Channels: " + str(channels) + "\n"
            QMessageBox.information(self, "File Information", reportstring, QMessageBox.Ok)
        except:
            pass

    # Clears the render list and screen.
    def clearImage(self):
        self.rl.clear()
        self.canvas.update()

    # Opens a wav file for rendering and playing.  The file data ia not stored internally
    # since it must be streamed from the file in other functions.  The filename is all that
    # is stored.
    def openFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Wav File",
                                                   "", "Wav Files (*.wav);;All Files (*.*)")

        if file_name:
            try:
                # Check opening
                samplingfreq, sound = wavfile.read(file_name)
                af = wave.open(file_name, 'rb')
                af.close()

                self.loadedFilename = file_name
                self.updateProgramWindowTitle()
            except:
                QMessageBox.warning(self, "File Not Loaded", "The file " + file_name + " could not be loaded.",
                                    QMessageBox.Ok)

    # Copies the current image to the system clipboard.
    def copyImageToClipboard(self):
        pixmap = QPixmap(self.canvas.size())
        self.canvas.render(pixmap)
        self.clipboard.setPixmap(pixmap)

    # Saves the current image to an image file.  Defaults to a png file but the file type
    # is determined by the extension on the filename the user selects.
    def saveAsImage(self):
        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['PNG Files (*.png)', 'JPEG Files (*.jpg)', 'Bitmap Files (*.bmp)'])
        dialog.setWindowTitle('Save Image As')

        if dialog.exec() == QDialog.Accepted:
            ext = "png"
            list = dialog.selectedNameFilter().split(" ")
            ext = list[len(list) - 1][3:-1]
            dialog.setDefaultSuffix(ext)

            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                try:
                    pixmap = QPixmap(self.canvas.size())
                    self.canvas.render(pixmap)
                    pixmap.save(file_name)
                except:
                    QMessageBox.warning(self, "File Not Saved", "The file " + file_name + " could not be saved.",
                                        QMessageBox.Ok)

    # Prints the current image to the printer using the selected printer options from the
    # options list.  This function does some initial setup, calls the print dialog box for
    # user input, and then calls printPreview which invokes the printing.
    def printImage(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        printer.setDocName("MusicImage")

        leftoffset = 36
        topoffset = 36

        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Landscape,
                         QMarginsF(leftoffset, topoffset, 36, 36))
        printer.setPageLayout(pl)
        if dialog.exec() == QDialog.Accepted:
            self.printPreview(printer)

    # Invokes a print preview of the current image using the selected printer options from the
    # options list.  This function does some initial setup, calls the print preview dialog box,
    # and then calls printPreview which invokes the printing.
    def printPreviewImage(self):
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("MusicImage")

        leftoffset = 36
        topoffset = 36

        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                         QMarginsF(leftoffset, topoffset, 36, 36))
        printer.setPageLayout(pl)

        dialog.paintRequested.connect(self.printPreview)
        dialog.exec()

    # This function does the printing by invoking an off-screen version of the image viewer and
    # rendering it to a pixmap.  This pixmap is then drawn as an image to the painter object
    # attached to the printer.
    def printPreview(self, printer):
        printviewer = ObjectListViewer(self, self.mainapp)
        printres = printer.resolution()

        wid = 7 * printres
        hei = wid * self.canvas.height() / self.canvas.width()
        printviewer.setFixedSize(QSize(round(wid), round(hei)))
        printviewer.zoomfactor = self.canvas.zoomfactor
        printviewer.center = self.canvas.center
        pixmap = QPixmap(printviewer.size())
        printviewer.render(pixmap)
        painter = QPainter(printer)
        painter.drawPixmap(QPoint(0, 0), pixmap)
        painter.end()

    # Ending dummy function for print completion.
    def print_completed(self, success):
        pass  # Nothing needs to be done.


if __name__ == '__main__':
    """
    Initiate the program. 
    """
    app = QApplication(sys.argv)
    window = MusicPainter(app)
    progcss = appcss()
    app.setStyleSheet(progcss.getCSS())
    sys.exit(app.exec_())
