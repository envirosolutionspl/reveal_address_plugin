from qgis.core import QgsNetworkAccessManager, QgsPointXY
from qgis.gui import QgsMapToolEmitPoint, QgsMapTool, QgsMapCanvas
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, Qgis, QgsSettings
from qgis.PyQt.QtWidgets import QMessageBox, QAction, QToolBar, QDialog
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QCoreApplication
from qgis.PyQt.QtGui import QIcon
import json
import os
from .utils import QgsTools

"""Wersja wtyczki"""
from . import PLUGIN_NAME as plugin_name
from . import PLUGIN_VERSION as plugin_version

class RevealAddressMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.coord_transform = QgsCoordinateTransform(canvas.mapSettings().destinationCrs(), 
            QgsCoordinateReferenceSystem.fromEpsgId(4326), 
            canvas.mapSettings().transformContext()
        )
        self.nam = QgsNetworkAccessManager.instance()
        self.qgs_tools = QgsTools()

    def canvasReleaseEvent(self, event):
        click_coords = self.toMapCoordinates(event.pos())
        click_coords_4326 = self.coord_transform.transform(click_coords)
        url = (f"https://nominatim.openstreetmap.org/reverse?format=json"
               f"&lat={click_coords_4326.y()}&lon={click_coords_4326.x()}"
        )
        req = QNetworkRequest(QUrl(url))          
        reply = self.nam.get(req)
        result = reply.finished.connect(self.handleResult)

        if result:
            self.canvas.unsetMapTool(self)

    def handleResult(self):
        reply = self.sender()
        err = reply.error()
        try:
            no_error = QNetworkReply.NetworkError.NoError
        except AttributeError:
            no_error = QNetworkReply.NoError

        if err != no_error:
            msg = f"Request error: {err}"
            self.qgs_tools.pushLogCritical(msg)
            return
        
        address_json = json.loads(str(reply.readAll(), 'utf-8'))

        if "display_name" in address_json:
            address = address_json["display_name"]
        else:
            address = "No address found"

        QMessageBox.information(None, "Address", address)

        return True


class RevealAddressPlugin:
    def __init__(self, iface, test_mode=False):
        self.map_tool = None
        self.action = None
        self.settings = QgsSettings()
        self.test_mode = test_mode

        if not self.test_mode:
            if Qgis.QGIS_VERSION_INT >= 31000:
                try:
                    from .qgis_feed import QgisFeed, QgisFeedDialog
                    from . import PLUGIN_NAME
                    self.selected_industry = self.settings.value("selected_industry", None)
                    show_dialog = self.settings.value("showDialog", True, type=bool)

                    if self.selected_industry is None and show_dialog:
                        self.showBranchSelectionDialog()

                    select_indust_session = self.settings.value('selected_industry')

                    self.feed = QgisFeed(selected_industry=select_indust_session, 
                                         plugin_name=PLUGIN_NAME)
                    self.feed.initFeed()
                except ImportError:
                    print("Pominięto ładowanie QgisFeed (ImportError lub Test Mode)")

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = os.path.join(self.plugin_dir, 'icons', 'icon.svg')
        self.actions = []
        self.menu = u'&EnviroSolutions'
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'EnviroSolutions')
        
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar(u'EnviroSolutions')
            self.toolbar.setObjectName(u'EnviroSolutions')
            
        self.shortcut = None
        self.first_start = None

    def addAction(
                self,
                icon_path,
                text,
                callback,
                enabled_flag=True,
                add_to_menu=True,
                add_to_toolbar=True,
                status_tip=None,
                whats_this=None,
                parent=None):

            icon = QIcon(icon_path)
            action = QAction(icon, text, parent)
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)

            if status_tip is not None:
                action.setStatusTip(status_tip)

            if whats_this is not None:
                action.setWhatsThis(whats_this)

            if add_to_toolbar:
                self.toolbar.addAction(action)

            if add_to_menu:
                self.iface.addPluginToMenu(
                    self.menu,
                    action)

            self.actions.append(action)

            return action

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('RevealAddressPlugin', message)
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.addAction(
            self.icon_path,
            text=self.tr(u'Reveal Address'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

        self.first_start = True

    def run(self):
        self.map_tool = RevealAddressMapTool(self.iface.mapCanvas())
        self.iface.mapCanvas().setMapTool(self.map_tool)

    def showBranchSelectionDialog(self):
        self.qgisfeed_dialog = QgisFeedDialog()

        if self.qgisfeed_dialog.exec_() == QDialog.Accepted:
            self.selected_branch = self.qgisfeed_dialog.comboBox.currentText()
            
            #Zapis w QGIS3.ini
            self.settings.setValue("selected_industry", self.selected_branch)  
            self.settings.setValue("showDialog", False)
            self.settings.sync()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if hasattr(self, 'actions'):
                    for action in self.actions:
                        self.iface.removePluginMenu(
                            u'&EnviroSolutions',
                            action)

        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.clear() 
            self.toolbar = None 
            
        if hasattr(self, 'map_tool') and self.map_tool:
            self.iface.mapCanvas().unsetMapTool(self.map_tool)