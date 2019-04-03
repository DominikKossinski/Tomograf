import math
import os
import sys
import threading
from datetime import datetime
from time import sleep

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, \
    QLineEdit, QCalendarWidget, QPlainTextEdit, QPushButton, QCheckBox, QFileDialog, QMessageBox, QSlider
from matplotlib import image as Image
from matplotlib import pyplot as plt
from pydicom import dcmread
from pydicom.dataset import Dataset, FileDataset
from skimage.draw import line


def loadImg(path):
    return cv2.imread(path)


def loop(w):
    w.repaint()
    sleep(0.5)


class App(QWidget):
    font = QFont('SansSerif', 10)
    label_width = 300
    text_area_width = 700

    def __init__(self):
        super().__init__()
        self.title = "Tomograf"
        self.width = 1600
        self.height = 900
        self.imgSize = 300
        self.left = 10
        self.top = 10
        scroll_area = QScrollArea(self)
        scroll_area.width = 1000

        grid = QVBoxLayout()
        grid_widget = QWidget()
        grid_widget.setLayout(grid)

        self.input_row = PatientInfoRow()
        self.center_widget = CenterRow(grid, "result_filtered.png", "sinogram.png", "result_filtered.png",
                                       self.input_row)
        grid.addWidget(self.center_widget)

        self.input_row = PatientInfoRow()
        grid.addWidget(self.input_row)

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(grid_widget)
        scroll_area.setGeometry(0, 0, self.width, self.height)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.initUi()

    def initUi(self):
        threading.Thread(target=loop, args=(self,)).start()
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()
        srcImg = loadImg(self.center_widget.path)
        self.center_widget.srcImage.setImg(srcImg)


class CenterRow(QWidget):

    def __init__(self, parent_layout, src_img, sinogram, result, input_row):
        super().__init__()
        self.parent_layout = parent_layout
        self.input_row = input_row
        self.path = "zdj/Kwadraty2.jpg"
        self.layout = QHBoxLayout()
        self.setFixedWidth(1500)
        self.thread = None
        self.working = False
        self.step = 0

        self.left_widget = QWidget()
        self.layout.addWidget(self.left_widget)

        self.left_layout = QHBoxLayout()
        self.left_widget.setFixedWidth(1200)

        self.srcImg = src_img
        self.srcImage = MyImage("Obrazek:", src_img, 300, 300)
        self.left_layout.addWidget(self.srcImage)

        self.sinogram = sinogram
        self.sinogramImage = MyImage("Sinogram:", sinogram, 300, 300)
        self.left_layout.addWidget(self.sinogramImage)

        self.result = result
        self.resultImage = MyImage("Wynik:", self.result, 300, 300)
        self.left_layout.addWidget(self.resultImage)

        self.left_widget.setLayout(self.left_layout)

        self.right_widget = QWidget()
        self.layout.addWidget(self.right_widget)

        self.right_layout = QVBoxLayout()

        self.img_button = QPushButton("Wybierz obraz")
        self.img_button.setFont(App.font)
        self.right_layout.addWidget(self.img_button)
        self.img_button.clicked.connect(self.change_file)

        self.countLabel = QLabel("Ilość detektorów:")
        self.countLabel.setFont(App.font)
        self.right_layout.addWidget(self.countLabel)

        self.countInput = QLineEdit()
        self.countInput.width = App.label_width
        self.right_layout.addWidget(self.countInput)

        self.angleLabel = QLabel("Krok układu ∆α:")
        self.angleLabel.setFont(App.font)
        self.right_layout.addWidget(self.angleLabel)

        self.angleInput = QLineEdit()
        self.angleInput.width = App.label_width
        self.right_layout.addWidget(self.angleInput)

        self.iLabel = QLabel("Rozpiętość układu emiter/detektor:")
        self.iLabel.setFont(App.font)
        self.right_layout.addWidget(self.iLabel)

        self.iInput = QLineEdit()
        self.iInput.width = App.label_width
        self.right_layout.addWidget(self.iInput)

        self.showCheckBox = QCheckBox("Pokazuj kroki")
        self.showCheckBox.setFont(App.font)
        self.showCheckBox.setChecked(True)
        self.right_layout.addWidget(self.showCheckBox)

        self.filter_check_box = QCheckBox("Filtruj")
        self.filter_check_box.setFont(App.font)
        self.filter_check_box.setChecked(True)
        self.right_layout.addWidget(self.filter_check_box)

        self.startButton = QPushButton("Rozpocznij przetwarzanie")
        self.startButton.setFont(App.font)
        self.right_layout.addWidget(self.startButton)
        self.startButton.clicked.connect(self.startButtonClick)

        self.show_points_button = QPushButton("Pokaż zapisane kroki")
        self.show_points_button.setFont(App.font)
        self.right_layout.addWidget(self.show_points_button)
        self.show_points_button.setVisible(False)
        self.show_points_button.clicked.connect(self.show_button_click)

        self.progressLabel = QLabel("")
        self.progressLabel.setFont(App.font)
        self.right_layout.addWidget(self.progressLabel)

        self.right_layout.addWidget(self.countLabel)

        self.right_widget.setLayout(self.right_layout)

        self.points_widget = QWidget()
        self.parent_layout.addWidget(self.points_widget)

        self.slider = QSlider(Qt.Horizontal)
        self.points_image = MyImage(" stopni", "zdj/Kwadraty2.jpg", 300, 300)
        self.setLayout(self.layout)

    def change_file(self):
        self.path = QFileDialog.getOpenFileName(self, 'Open File')[0]
        self.srcImage.set_image(self.path)
        print("Path = '", self.path, "'")

    def show_button_click(self):
        layout = QVBoxLayout()
        self.points_widget = QWidget()
        self.points_widget.setLayout(layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedWidth(App.label_width)
        self.slider.setMinimum(0)
        self.slider.setMaximum(math.floor(self.step / 10) * 10)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(10)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.slider_change)

        self.points_image.setText("0 stopni")
        self.points_image.set_image("points/point_0.png")
        layout.addWidget(self.points_image)
        layout.addWidget(self.slider)
        self.parent_layout.addWidget(self.points_widget)

    def slider_change(self):
        try:
            val = self.slider.value()
            if val % 10 != 0:
                val = math.floor(val / 10) * 10
                self.slider.setValue(val)
            self.points_image.set_image("points/point_" + str(val) + ".png")
            self.points_image.setText(str(int(val * 360 / self.step)) + " stopni")
        except Exception as e:
            print(str(e))

    def startButtonClick(self):
        if not self.working:
            files = os.listdir("points")
            self.show_points_button.setVisible(False)
            self.points_widget.setLayout(QVBoxLayout())
            self.parent_layout.removeWidget(self.points_widget)
            for f in files:
                os.remove("points/" + str(f))
            img = loadImg(self.path)
            imgSize = (len(img), len(img[0]), len(img[0][0]))
            try:
                i = float(self.iInput.text())
                n = int(self.countInput.text())
                alpha = float(self.angleInput.text())
                self.step = int(360 / alpha)
                if self.thread is not None:
                    print("Stopping Thread")
                    self.thread._stop()
                    self.thread = None
                self.thread = threading.Thread(
                    target=generateSinogram,
                    args=(img, imgSize, alpha,
                          n, i, self.showCheckBox.isChecked(), self.filter_check_box.isChecked(), self.resultImage,
                          self.sinogramImage,
                          self.srcImage, self,)
                )
                self.thread.start()
                self.working = True
            except ValueError:
                QMessageBox.about(self, "Dane", "Wprowadź poprawne dane przetwarzenia")
                print("Error")
        else:
            print("working")

    def showAlert(self):
        print("Running")


class PatientInfoRow(QWidget):

    def __init__(self):
        super().__init__()
        # self.setFixedWidth(1200)

        self.layout = QHBoxLayout()

        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(App.label_width + 40)
        self.layout.addWidget(self.left_widget)

        self.left_layout = QVBoxLayout()

        self.firstNameLabel = QLabel("Imię:")
        self.firstNameLabel.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.firstNameLabel)
        self.firstNameLabel.setFont(App.font)

        self.firstNameInput = QLineEdit()
        self.firstNameInput.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.firstNameInput)
        self.firstNameInput.width = App.label_width

        self.lastNameLabel = QLabel("Nazwisko")
        self.lastNameLabel.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.lastNameLabel)
        self.lastNameLabel.setFont(App.font)

        self.lastNameInput = QLineEdit()
        self.lastNameInput.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.lastNameInput)
        self.lastNameInput.width = App.label_width

        self.peselLabel = QLabel("Pesel:")
        self.peselLabel.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.peselLabel)
        self.peselLabel.setFont(App.font)

        self.peselInput = QLineEdit()
        self.peselInput.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.peselInput)
        self.peselInput.width = App.label_width

        self.dateLabel = QLabel("Data badania:")
        self.dateLabel.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.dateLabel)
        self.dateLabel.setFont(App.font)

        self.dateInput = QCalendarWidget()
        self.dateInput.setFixedWidth(App.label_width)
        self.left_layout.addWidget(self.dateInput)
        self.dateInput.width = App.label_width

        self.left_widget.setLayout(self.left_layout)

        self.right_widget = QWidget()
        self.layout.addWidget(self.right_widget)
        self.right_layout = QVBoxLayout()

        self.commentLabel = QLabel("Komentarz:")
        self.right_layout.addWidget(self.commentLabel)
        self.commentLabel.setFont(App.font)

        self.commentTextArea = QPlainTextEdit()
        self.right_layout.addWidget(self.commentTextArea)
        self.commentTextArea.setFixedWidth(App.text_area_width)

        self.acceptButton = QPushButton("Zapisz")
        self.right_layout.addWidget(self.acceptButton)
        self.acceptButton.setFont(App.font)
        self.acceptButton.setFixedWidth(App.label_width)

        self.loadButton = QPushButton("Otwórz z pliku")
        self.right_layout.addWidget(self.loadButton)
        self.loadButton.setFont(App.font)
        self.loadButton.setFixedWidth(App.label_width)

        self.loadButton.clicked.connect(self.load_file)

        self.acceptButton.clicked.connect(self.accept_button_on_click)

        self.right_widget.setLayout(self.right_layout)

        self.imageWidget = QWidget()
        self.imageLayout = QVBoxLayout()
        self.imageWidget.setLayout(self.imageLayout)

        self.image = QLabel()
        self.label = QLabel("Zapisany obraz:")
        self.label.setFont(App.font)
        self.imageLayout.addWidget(self.label)
        self.label.setVisible(False)
        self.imageLayout.addWidget(self.image)
        self.imageWidget.width = 300

        self.layout.addWidget(self.imageWidget)

        self.setLayout(self.layout)

    def load_file(self):
        path = QFileDialog.getOpenFileName(self, 'Open File')[0]
        try:
            ds = dcmread(path, force=True)

            patientName = str(ds.PatientName)
            firstName = patientName[:patientName.index("^")]
            lastName = patientName[patientName.index("^") + 1:]
            pesel = str(ds.PatientID)
            self.firstNameInput.setText(firstName)
            self.lastNameInput.setText(lastName)
            self.peselInput.setText(pesel)
            self.commentTextArea.setPlainText(str(ds.ImageComments))

            self.dateInput.setSelectedDate(datetime.strptime(str(ds.ContentDate), '%Y%m%d'))

            cols = int(ds.Columns)
            rows = int(ds.Rows)
            img = np.frombuffer(ds.PixelData, dtype=np.uint8)
            image = to3DArray(img, cols, rows)
            print(image)
            Image.imsave('fromDcm.png', image)
            pixMap = QPixmap("fromDcm.png")
            pixMap = pixMap.scaled(300, 300, Qt.KeepAspectRatio)
            self.label.setVisible(True)
            self.image.setPixmap(pixMap)
            print(img)

        except Exception as e:
            print(str(e))

    def accept_button_on_click(self):
        try:
            file_meta = Dataset()
            file_meta.ImplementationClassUID = "1.2.3.4"
            print("257")
            file_meta.MediaStorageSOPInstanceUID = "1.2.3"
            file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'

            data_set = FileDataset(self.firstNameInput.text() + self.lastNameInput.text() + ".dcm", {},
                                   file_meta=file_meta, preamble=b"\0" * 128)
            data_set.is_little_endian = True
            data_set.is_implicit_VR = True
            data_set.PatientName = self.firstNameInput.text() + "^" + self.lastNameInput.text()
            data_set.PatientID = self.peselInput.text()
            data_set.ContentDate = self.dateInput.selectedDate().toString("yyyyMMdd")
            data_set.ContentTime = "666666"
            data_set.ImageComments = self.commentTextArea.toPlainText()

            result = loadImg("result_filtered.png")
            (result, col, rows) = to2DArray(result)
            data_set.PhotometricInterpretation = "RGB"
            data_set.SamplesPerPixel = 3
            data_set.PlanarConfiguration = 1
            data_set.Columns = col
            data_set.Rows = rows
            data_set.PixelData = np.array(result, np.int8).tostring()

            data_set.save_as(self.firstNameInput.text() + self.lastNameInput.text() + ".dcm", False)
            print("Save sucessvull")
            QMessageBox.about(self, "Zapis", "Pomyślnie zapisano plik")
        except Exception as e:
            QMessageBox.about(self, "Zapis", "Nastąpił błąd podczas zapisywania")
            print(str(e))


class MyImage(QWidget):

    def __init__(self, text, path, width, img_size):
        super().__init__()
        self.layout = QVBoxLayout()
        self.imgSize = img_size
        self.width = width
        self.height = img_size + 35
        self.textLabel = QLabel()
        self.textLabel.setText(text)
        self.layout.addWidget(self.textLabel)
        self.textLabel.setFixedWidth(width)
        self.textLabel.setFixedHeight(30)
        self.textLabel.setFont(QFont('SansSerif', 15))
        self.pixMapLabel = QLabel()
        self.layout.addWidget(self.pixMapLabel)
        self.pixMapLabel.setFixedWidth(img_size)
        self.pixMapLabel.setFixedHeight(img_size)
        self.set_image(path)

        self.setLayout(self.layout)

    def setText(self, text):
        self.textLabel.setText(text)

    def set_image(self, path, resize=True):
        pixMap = QPixmap(path)
        if resize:
            pixMap = pixMap.scaled(300, 300, Qt.KeepAspectRatio)
        self.pixMapLabel.setPixmap(pixMap)

    def setImg(self, im, resize=True, name="none"):
        Image.imsave(name + '.png', im)
        pixMap = QPixmap(name + ".png")
        if resize:
            pixMap = pixMap.scaled(300, 300, Qt.KeepAspectRatio)
        self.pixMapLabel.setPixmap(pixMap)


def average(img):
    suma = 0
    count = 0
    for i in img:
        for j in i:
            suma += j[0]
            count += 1
    return suma / count


class Result:

    def __init__(self, result):
        self.m_res = []
        for a in result:
            self.m_res.append(math.floor(a * 255))


def generateSinogram(img, imgSize, alpha, n, l, showSteps, enable_filter, resultLabel, sinogramLabel, srcImage, app):
    steps = int(360 / alpha) + 1
    r = (imgSize[0] ** 2 + imgSize[1] ** 2) ** 0.5 / 2
    print(imgSize)
    srcImage.setImg(img)
    avg = average(img)
    print("avg = ", avg)
    result = np.zeros(imgSize)
    resultLabel.setImg(result)
    sinogram = np.zeros((steps, n, 3))
    sinogramLabel.setImg(sinogram, False)
    stepsTabs = []
    kernel = generate(n)
    points = np.zeros((imgSize[0], imgSize[1], 1))
    for i in range(steps):
        app.progressLabel.setText("Postęp " + str(int(i / steps * 100)) + "%")
        fi = i * alpha
        x0 = int(r * math.cos(math.radians(fi)) + imgSize[1] / 2)
        y0 = int(r * math.sin(math.radians(fi)) + imgSize[0] / 2)

        sumTab = []
        xTabs = []
        yTabs = []
        for j in range(n):

            x1 = int(r * math.cos(math.radians(fi) + math.pi - (math.radians(l) / 2) +
                                  j * (math.radians(l) / (n - 1))) + imgSize[1] / 2)
            y1 = int(r * math.sin(math.radians(fi) + math.pi - (math.radians(l) / 2) +
                                  j * (math.radians(l) / (n - 1))) + imgSize[0] / 2)

            xtab, ytab = line(x0, y0, x1, y1)

            suma = 0
            count = 0
            for k in range(len(xtab)):
                point = (xtab[k], ytab[k])
                if 0 <= point[0] < imgSize[1] and 0 <= point[1] < imgSize[0]:
                    suma += img[point[1]][point[0]][0]
                    count += 1
            if count != 0:
                suma /= count
            # suma /= 255
            sumTab.append(suma)
            xTabs.append(xtab)
            yTabs.append(ytab)
        sumTab1 = np.convolve(sumTab, kernel, "same")  # filter_row(sumTab1)
        for a in range(len(sumTab)):
            suma = sumTab[a] / 255
            sinogram[i][a] += [suma, suma, suma]
            suma = sumTab1[a] / 255
            suma = suma
            xtab = xTabs[a]
            ytab = yTabs[a]
            for k in range(len(xtab)):
                point = (xtab[k], ytab[k])
                if imgSize[1] > point[0] >= 0 <= point[1] < imgSize[0]:
                    result[point[1]][point[0]] += [suma, suma, suma]
                    if result[point[1]][point[0]][0] > 1:
                        result[point[1]][point[0]] = [1, 1, 1]
                    if result[point[1]][point[0]][0] < 0:
                        result[point[1]][point[0]] = [0, 0, 0]
        if fi % 1 == 0:
            print("Angle = ", fi)
        if showSteps:
            resultLabel.setImg(result, True)
            sinogramLabel.setImg(sinogram, True)
        if i % 10 == 0:
            Image.imsave("points/point_" + str(i) + ".png", result)
    print("Len = ", len(stepsTabs))
    avgr = average(result)
    Image.imsave('result_no_correction.png', result)
    print("Result avg = ", avgr)
    if enable_filter:
        result = filter(result, 3, 3)
    resultLabel.setImg(result)
    sinogram = normalizeAll(sinogram)
    sinogramLabel.setImg(sinogram, True)
    Image.imsave('sinogram.png', sinogram)
    Image.imsave('result_filtered.png', result)
    app.working = False
    print("Rows = ", result.shape[0], " Col = ", result.shape[1])
    app.show_points_button.setVisible(True)
    error = calc(img, result)
    app.progressLabel.setText("Błąd (RMSE): " + str(round(error, 5)))
    return


def normalizeAll(sumTab):
    mX = 0
    mI = 255
    for i in sumTab:
        for j in i:
            mX = max(mX, j[0])
            mI = min(mI, j[0])
    print("Max = ", mX, " Min = ", mI)
    if mX != 0:
        for i in range(len(sumTab)):
            for j in range(len(sumTab[i])):
                for a in range(3):
                    sumTab[i][j][a] = (sumTab[i][j][a] - mI) / (mX - mI)
    return sumTab


def to2DArray(img):
    tab = []
    for a in range(3):
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                tab.append(math.floor(img[i][j][0]))
    return (tab, img.shape[0], img.shape[1])


def to3DArray(img, cols, rows):
    result = np.zeros((rows, cols, 3))
    i = 0
    j = 0
    for a in range(int(len(img) / 3)):
        result[i][j] = img[a] / 255
        j += 1
        if j >= rows:
            j = 0
            i += 1
    return result


def generate(size):
    tab = []
    for i in range(size):
        if i == size // 2:
            tab.append(1)
        else:
            if abs(i - size / 2) % 2 == 0:
                tab.append(0)
            else:
                tab.append(-4 / math.pi ** 2 * (1 / (abs(i - size // 2) ** 2)))
    return tab

def calc(img, result):
    suma = 0
    count = 0
    for i in range(len(img)):
        for j in range(len(img[i])):
            suma += (img[i][j][0] / 255 - result[i][j][0]) ** 2
            count += 1
    print("Suma = ", suma)
    print("Count = ", count)
    print("Błąd = ", suma / count)
    return suma / count


def filter(result, n, size):
    mask = np.ones((size, size))
    l = 0
    for i in mask:
        for j in i:
            l += j
    if l == 0:
        return
    for a in range(n):
        for i in range(len(result)):
            for j in range(len(result[0])):
                if i - int(len(mask) / 2) >= 0 and i + int(len(mask) / 2) < len(result) \
                        and j - int(len(mask[0]) / 2) >= 0 and j + int(len(mask[0]) / 2) < len(result[0]):
                    sum = 0
                    for a in range(-int(len(mask) / 2), int(len(mask) / 2) + 1):
                        for b in range(-int(len(mask) / 2), int(len(mask) / 2) + 1):
                            sum += result[i + a][j + b][0] * mask[a + 1][b + 1]
                    result[i][j] = sum / l
    return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
