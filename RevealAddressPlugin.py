from qgis.core import QgsNetworkAccessManager, QgsPointXY
from qgis.gui import QgsMapToolEmitPoint, QgsMapTool, QgsMapCanvas
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem
from qgis.PyQt.QtWidgets import QMessageBox, QAction, QToolBar
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QCoreApplication
from qgis.PyQt.QtGui import QIcon
import json
import os

class RevealAddressMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.coord_transform = QgsCoordinateTransform(canvas.mapSettings().destinationCrs(), 
            QgsCoordinateReferenceSystem.fromEpsgId(4326), 
            canvas.mapSettings().transformContext()
        )
        self.nam = QgsNetworkAccessManager.instance()

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
        except:
            no_error = QNetworkReply.NoError
        
        if err != no_error:
            print("Request error: ", err)
            return
        
        address_json = json.loads(str(reply.readAll(), 'utf-8'))

        if "display_name" in address_json:
            address = address_json["display_name"]
        else:
            address = "No address found"

        QMessageBox.information(None, "Address", address)

        return True


class RevealAddressPlugin:
    def __init__(self, iface):
        self.map_tool = None
        self.action = None
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