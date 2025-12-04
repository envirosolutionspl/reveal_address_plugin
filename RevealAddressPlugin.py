from qgis.core import QgsNetworkAccessManager, QgsPointXY
from qgis.gui import QgsMapToolEmitPoint, QgsMapTool, QgsMapCanvas
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem
from qgis.PyQt.QtWidgets import QMessageBox, QAction, QToolBar
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QCoreApplication
from qgis.PyQt.QtGui import QIcon
import json
import os

"""Wersja wtyczki"""
plugin_name = "Reveal address"
plugin_version = "1.3.0"

class RevealAddressMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

        # Create a coordinate transform object to transform the coordinates from the canvas CRS to WGS 84
        self.coord_transform = QgsCoordinateTransform(canvas.mapSettings().destinationCrs(), QgsCoordinateReferenceSystem(4326), canvas.mapSettings().transformContext())

        # Create a QgsNetworkAccessManager object
        self.nam = QgsNetworkAccessManager.instance()

    def canvasReleaseEvent(self, event):
        # Get the click coordinates
        click_coords = self.toMapCoordinates(event.pos())

        # Transform the coordinates from the canvas CRS to WGS 84
        click_coords_4326 = self.coord_transform.transform(click_coords)

        # Create a GET request to the Nominatim API with the lat and lon of the click
        url = "https://nominatim.openstreetmap.org/reverse?format=json&lat={}&lon={}".format(click_coords_4326.y(), click_coords_4326.x())
        req = QNetworkRequest(QUrl(url))

        # Send the GET request and connect the finished signal to the self.handleResult() method
        reply = self.nam.get(req)
        result = reply.finished.connect(self.handleResult)

        if result:
            self.canvas.unsetMapTool(self)

    def handleResult(self):
        reply = self.sender()
        if reply.error() != QNetworkReply.NoError:
            print("Request error: ", reply.error())
            return
        address_json = json.loads(str(reply.readAll(), 'utf-8'))
        if "display_name" in address_json:
            address = address_json["display_name"]
        else:
            address = "No address found"

        # Show the address in a message box
        QMessageBox.information(None, "Address", address)
        
        return True


class RevealAddressPlugin:
    def __init__(self, iface):
        self.map_tool = None
        self.action = None
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = f'{self.plugin_dir}\icons\icon.svg'

        self.actions = []
        self.menu = u'&EnviroSolutions'
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'EnviroSolutions')
        
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar(u'EnviroSolutions')
            self.toolbar.setObjectName(u'EnviroSolutions')
            
        self.shortcut = None
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    def add_action(
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

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('RevealAddressPlugin', message)
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.add_action(
            self.icon_path,
            text=self.tr(u'Reveal Address'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )
        
        # will be set False in run()
        self.first_start = True

    def run(self):
        # Create and set the map tool
        self.map_tool = RevealAddressMapTool(self.iface.mapCanvas())
        self.iface.mapCanvas().setMapTool(self.map_tool)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                u'&EnviroSolutions',
                action)
            # self.iface.removeToolBarIcon(action)
            self.toolbar.removeAction(action)
                
        # Remove the map tool and action when the plugin is unloaded
        if self.map_tool:
            self.iface.mapCanvas().unsetMapTool(self.map_tool)

        # remove the toolbar
        del self.toolbar
