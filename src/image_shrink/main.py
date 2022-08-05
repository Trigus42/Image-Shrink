import io
import math
import os
import sys
from multiprocessing.pool import ThreadPool
from typing import Dict, List

import psutil
from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

def SaveImageWithTargetSize(path, new_path, target: float|int):
   im = Image.open(path)

   # If image already has the desired size, save using same quality settings
   if os.path.getsize(path) <= target:
      im.save(new_path, quality="keep")
      return
   
   # Min and Max quality
   Qmin, Qmax = 0, 96
   # Highest acceptable quality found
   Qacc = -1
   while Qmin <= Qmax:
      m = math.floor((Qmin + Qmax) / 2)

      # Encode into memory and get size
      buffer = io.BytesIO()
      im.save(buffer, format=im.format, quality=m)
      s = buffer.getbuffer().nbytes

      if s <= target:
         Qacc = m
         Qmin = m + 1
      elif s > target:
         Qmax = m - 1

   # Write to disk at the defined quality
   if Qacc > -1:
      im.save(new_path, quality=Qacc)
   else:
      print("ERROR: No acceptable quality factor found for: " + os.path.basename(path), file=sys.stderr)

def image_processing_threaded(self, image, target_size, total_pixels, output_dir):
    if self.image_processing["stopped"]:
        return

    # If the target_size is the total size, calculate the image size from the ratio of the image pixels to the total pixels
    if self.checkBox.isChecked():
        image_target_size = int((image["pixels"]/total_pixels)*target_size)
    else:
        image_target_size = target_size

    # If no output path is given, use the same path as the image and add a suffix
    if not output_dir:
        root, ext = os.path.splitext(image["path"])
        out_path = root + "_resized_" + str(target_size/1000000).rstrip('0').rstrip('.') + "MB" + ext
    else:
        out_path = output_dir + os.path.sep + os.path.basename(image["path"])

    try:
        SaveImageWithTargetSize(image["path"], out_path, image_target_size)
    except Exception as e:
        QtWidgets.QMessageBox.critical(self.centralwidget, "Error", str(e))

    self.image_processing["finished_images"] += 1
    self.progressBar.setValue( self.image_processing["finished_images"]/ self.image_processing["total_images"]*100)


class CustomTable(QtWidgets.QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.image_paths = set()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
    
    def dropEvent(self, e):
      image_paths_string: str = e.mimeData().text()
      image_paths = [os.path.normpath(path.split("file://")[1]) for path in image_paths_string.split("\n") if path.startswith("file://")]
      image_paths = [path for path in image_paths if os.path.isfile(path)]

      for path in image_paths:
        if path not in self.image_paths:
            self.image_paths.add(path)
            self.insertRow(self.rowCount())
            self.setItem(self.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(os.path.basename(path)))
            self.setItem(self.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(path))
            self.setItem(self.rowCount() - 1, 2, QtWidgets.QTableWidgetItem(str(int(os.path.getsize(path) / 1000))))


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Image Resizer")
        MainWindow.resize(575, 436)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tableWidget = CustomTable(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(10, 20, 551, 231))
        self.tableWidget.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.tableWidget.setWordWrap(False)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.lineEdit_target_size = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_target_size.setGeometry(QtCore.QRect(20, 310, 121, 32))
        self.lineEdit_target_size.setInputMethodHints(QtCore.Qt.ImhDigitsOnly|QtCore.Qt.ImhPreferNumbers)
        self.lineEdit_target_size.setObjectName("lineEdit")
        self.label_target_size = QtWidgets.QLabel(self.centralwidget)
        self.label_target_size.setGeometry(QtCore.QRect(20, 280, 111, 18))
        self.label_target_size.setObjectName("label")
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setGeometry(QtCore.QRect(20, 350, 111, 22))
        self.checkBox.setObjectName("checkBox")
        self.lineEdit_thread_count = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_thread_count.setGeometry(QtCore.QRect(155, 310, 81, 32))
        self.lineEdit_thread_count.setInputMethodHints(QtCore.Qt.ImhDigitsOnly|QtCore.Qt.ImhPreferNumbers)
        self.lineEdit_thread_count.setObjectName("lineEdit_2")
        self.label_thread_count = QtWidgets.QLabel(self.centralwidget)
        self.label_thread_count.setGeometry(QtCore.QRect(155, 280, 51, 18))
        self.label_thread_count.setObjectName("label_2")
        self.lineEdit_output = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_output.setGeometry(QtCore.QRect(250, 310, 311, 32))
        self.lineEdit_output.setObjectName("lineEdit_3")
        self.label_output = QtWidgets.QLabel(self.centralwidget)
        self.label_output.setGeometry(QtCore.QRect(250, 280, 101, 18))
        self.label_output.setObjectName("label_3")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(20, 385, 341, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setObjectName("progressBar")
        self.startButton = QtWidgets.QPushButton(self.centralwidget)
        self.startButton.setGeometry(QtCore.QRect(370, 380, 84, 34))
        self.startButton.setObjectName("pushButton")
        self.startButton.connect(self.startButton, QtCore.SIGNAL("clicked()"), self.startButtonAction)
        self.stopButton = QtWidgets.QPushButton(self.centralwidget)
        self.stopButton.setGeometry(QtCore.QRect(470, 380, 84, 34))
        self.stopButton.setObjectName("pushButton_2")
        self.stopButton.connect(self.stopButton, QtCore.SIGNAL("clicked()"), self.stopButtonAction)
        self.deleteButton = QtWidgets.QPushButton(self.centralwidget)
        self.deleteButton.setGeometry(QtCore.QRect(477, 260, 84, 34))
        self.deleteButton.setObjectName("pushButton_3")
        self.deleteButton.connect(self.deleteButton, QtCore.SIGNAL("clicked()"), self.deleteButtonAction)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def startButtonAction(self):
        # Get image path from table
        image_paths = [self.tableWidget.item(row, 1).text() for row in range(self.tableWidget.rowCount())]
        # Get target size from line edit and convert from kb to bytes
        target_size = float(self.lineEdit_target_size.text())*1000 if self.lineEdit_target_size.text().isdecimal() else 5000000
        # Get output path from line edit and check if it is a valid path
        output_dir = os.path.normpath(self.lineEdit_output.text()) if os.path.isdir(self.lineEdit_output.text()) else None

        images: List[Dict] = []

        total_pixels = 0
        for image_path in image_paths:
            try:
                im = Image.open(image_path)
                image_pixels = im.size[0] * im.size[1]
                total_pixels += image_pixels
                images.append({"path": image_path, "pixels": image_pixels})
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.centralwidget, "Error", str(e))

        self.image_processing = {}
        self.image_processing["stopped"] = False
        self.image_processing["finished_images"] = 0
        self.image_processing["total_images"] = len(images)

        threads = []
        thread_count = int(self.lineEdit_thread_count.text()) if self.lineEdit_thread_count.text().isdecimal() else int(psutil.cpu_count()*0.9)

        pool = ThreadPool(processes=thread_count)
        
        for image in images:
            threads.append(pool.apply_async(image_processing_threaded, args = (self, image, target_size, total_pixels, output_dir, )))

    def stopButtonAction(self):
         self.image_processing["stopped"] = True

    def deleteButtonAction(self):
        for item in self.tableWidget.selectedItems():
            self.tableWidget.removeRow(item.row())

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Image Shrinker"))
        self.tableWidget.setToolTip(_translate("MainWindow", "<html><head/><body><p>Drag and drop images here</p></body></html>"))
        self.tableWidget.setWhatsThis(_translate("MainWindow", "<html><head/><body><p><br/></p></body></html>"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Name"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Path"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Size (KB)"))
        self.lineEdit_target_size.setText(_translate("MainWindow", "5000"))
        self.label_target_size.setText(_translate("MainWindow", "Target size (KB)"))
        self.checkBox.setToolTip(_translate("MainWindow", "<html><head/><body><p>Apply target size limit to all files\' combined size</p></body></html>"))
        self.checkBox.setText(_translate("MainWindow", "Combined size"))
        self.lineEdit_output.setToolTip(_translate("MainWindow", "<html><head/><body><p>If left empty, images will be placed in same dir with a suffix</p></body></html>"))
        self.label_output.setText(_translate("MainWindow", "Ouput directory"))
        self.startButton.setText(_translate("MainWindow", "Start"))
        self.stopButton.setText(_translate("MainWindow", "Stop"))
        self.deleteButton.setText(_translate("MainWindow", "Delete"))
        self.deleteButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Delete selected items from list</p></body></html>"))
        self.label_thread_count.setText(_translate("MainWindow", "Threads"))
        self.lineEdit_thread_count.setToolTip(_translate("MainWindow", "<html><head/><body><p>Number of threads to use (images to process in parallel)</p></body></html>"))
        self.lineEdit_thread_count.setText(str(int(psutil.cpu_count()*0.9)))

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())

if __name__ == '__main__':
   main()