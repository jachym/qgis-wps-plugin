# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoDataDialog
                                 A QGIS plugin
 This plugin gathers cz/sk data sources.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-08-04
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Test
        email                : test
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import webbrowser

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt import QtGui
from qgis.utils import iface
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.gui import *

from .connect import *

owslib_exists = True
try:
    from owslib.wps import WebProcessingService
    from owslib.wps import ComplexDataInput
    from owslib.util import getTypedValue
except:
    owslib_exists = False

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'wps_dialog_base.ui'))


class WpsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(WpsDialog, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)
        self.pushButtonAbout.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons/cropped-opengeolabs-logo-small.png")))
        self.pushButtonAbout.clicked.connect(self.showAbout)
        if owslib_exists and self.check_owslib_fix():
            self.pushButtonLoadProcesses.clicked.connect(self.load_processes)
            self.pushButtonLoadProcess.clicked.connect(self.load_process)
            self.verticalLayoutInputs = QVBoxLayout(self.tabInputs)
            self.pushButtonExecute.clicked.connect(self.execute_process)
            self.input_items = {}
        else:
            QMessageBox.information(None, QApplication.translate("WPS", "ERROR:", None), QApplication.translate("WPS", "You have to install OWSlib with fix.", None))

    def check_owslib_fix(self):
        try:
            val = getTypedValue('integer', None)
            return True
        except:
            return False

    def load_processes(self):
        self.textEditLog.append(QApplication.translate("WPS", "Loading processes ...", None))
        self.loadProcesses = GetProcesses()
        self.loadProcesses.setUrl(self.lineEditWpsUrl.text())
        self.loadProcesses.statusChanged.connect(self.on_load_processes_response)
        self.loadProcesses.start()

    def on_load_processes_response(self, response):
        if response.status == 200:
            self.comboBoxProcesses.clear()
            for proc in response.data:
                self.comboBoxProcesses.addItem(proc)
            self.pushButtonLoadProcess.setEnabled(True)
            self.textEditLog.append(QApplication.translate("WPS", "Processes loaded", None))
        else:
            QMessageBox.information(None, QApplication.translate("WPS", "ERROR:", None), QApplication.translate("WPS", "Error loading processes", None))
            self.textEditLog.append(QApplication.translate("WPS", "Error loading processes", None))

    def get_all_layers_input(self):
        return QgsMapLayerComboBox(self.tabInputs)

    def get_input(self, identifier, data_type, default_value):
        # TODO check types
        input_item = None
        if data_type == 'ComplexData':
            input_item = self.get_all_layers_input()
        else:
            input_item = QLineEdit(self.tabInputs)
            input_item.setText(str(default_value))
        hbox_layout = QHBoxLayout(self.tabInputs)
        label = QLabel(self.tabInputs)
        label.setText(str(identifier))
        hbox_layout.addWidget(label)
        hbox_layout.addWidget(input_item)
        # TODO check if there is not a better way
        self.input_items[str(identifier)] = input_item
        return hbox_layout

    def load_process(self):
        self.textEditLog.append(QApplication.translate("WPS", "Loading process ...", None))
        self.loadProcess = GetProcess()
        self.loadProcess.setUrl(self.lineEditWpsUrl.text())
        self.loadProcess.setIdentifier(self.comboBoxProcesses.currentText())
        self.loadProcess.statusChanged.connect(self.on_load_process_response)
        self.loadProcess.start()

    def on_load_process_response(self, response):
        if response.status == 200:
            if response.data.abstract is not None:
                for i in reversed(range(self.verticalLayoutInputs.count())):
                    for j in reversed(range(self.verticalLayoutInputs.itemAt(i).count())):
                        self.verticalLayoutInputs.itemAt(i).itemAt(j).widget().setParent(None)
                self.labelProcessDescription.setText(response.data.abstract)
                self.input_items = {}
                self.pushButtonExecute.setEnabled(True)
                for x in response.data.dataInputs:
                    input_item = self.get_input(x.identifier, x.dataType, x.defaultValue)
                    self.verticalLayoutInputs.addLayout(input_item)
                self.tabInputs.setLayout(self.verticalLayoutInputs)
            self.textEditLog.append(QApplication.translate("WPS", "Process loaded", None))
        else:
            QMessageBox.information(None, QApplication.translate("WPS", "ERROR:", None), QApplication.translate("WPS", "Error loading process", None))
            self.textEditLog.append(QApplication.translate("WPS", "Error loading process", None))

    def execute_process(self):
        # Async call: https://ouranosinc.github.io/pavics-sdi/tutorials/wps_with_python.html
        myinputs = []
        for x in self.input_items:
            print(x)
            print(self.input_items[x])
            if isinstance(self.input_items[x], QgsMapLayerComboBox):
                # TODO check input type and export into it (GML, GeoPackage, etc.)
                with open(os.path.join(os.path.dirname(__file__), 'tests', 'rain_sample_data.gml')) as fd:
                    cdi = ComplexDataInput(fd.read())
                myinputs.append((x, cdi))
            else:
                # TODO check also other types than just QLineEdit
                if self.input_items[x].text() != 'None':
                    myinputs.append((x, self.input_items[x].text()))
        self.textEditLog.append(QApplication.translate("WPS", "Executing process ...", None))
        self.executeProcess = ExecuteProcess()
        self.executeProcess.setUrl(self.lineEditWpsUrl.text())
        self.executeProcess.setIdentifier(self.comboBoxProcesses.currentText())
        self.executeProcess.setInputs(myinputs)
        self.executeProcess.statusChanged.connect(self.on_execute_process_response)
        self.executeProcess.start()

    def on_execute_process_response(self, response):
        if response.status == 200:
            self.textEditLog.append(QApplication.translate("WPS", "Process executed", None))
            # TODO check output type
            vector = QgsVectorLayer('/vsizip/' + response.filepath, "Process output", "ogr")
            if vector.isValid():
                QgsProject.instance().addMapLayer(vector)
                self.textEditLog.append(QApplication.translate("WPS", "Data loaded into the map", None))
            else:
                QMessageBox.information(None, QApplication.translate("WPS", "ERROR:", None), QApplication.translate("WPS", "Can not load output into map", None))
                self.textEditLog.append(QApplication.translate("WPS", "Can not load output into map", None))
                self.textEditLog.append(QApplication.translate("WPS", "Showing content of the file", None))
                self.appendFileContentIntoLog(response.filepath)
        else:
            QMessageBox.information(None, QApplication.translate("WPS", "ERROR:", None), QApplication.translate("WPS", "Error executing process", None))
            self.textEditLog.append(QApplication.translate("WPS", "Error executing process", None))
            self.textEditLog.append(response.data)

    def appendFileContentIntoLog(self, file):
        with (open(file, "r")) as f:
            self.textEditLog.append(str(f.read()))

    def showAbout(self):
        try:
            webbrowser.get().open("http://opengeolabs.cz")
        except (webbrowser.Error):
            self.iface.messageBar().pushMessage(QApplication.translate("GeoData", "Error", None), QApplication.translate("GeoData", "Can not find web browser to open page about", None), level=Qgis.Critical)
