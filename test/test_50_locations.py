# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch
import random
import time
from qgis.core import (
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsApplication, 
    QgsProject
)
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtWidgets import QMessageBox
from RevealAddressPlugin import RevealAddressMapTool
from constans import MIN_LAT, MAX_LAT, MIN_LON, MAX_LON

class TestRevealAddressPlugin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Ta metoda uruchamia się RAZ przed wszystkimi testami w tej klasie.
        Inicjuje aplikację QGIS, co jest niezbędne do tworzenia Widgetów (QgsMapCanvas).
        """
        cls.qgs = QgsApplication([], True)
        cls.qgs.initQgis()

    @classmethod
    def tearDownClass(cls):
        """
        Zamyka aplikację QGIS po zakończeniu testów.
        """
        cls.qgs.exitQgis()

    def setUp(self):
        """
        Uruchamia się przed każdym pojedynczym testem (def test_...).
        """
        self.canvas = QgsMapCanvas()
        self.canvas.setDestinationCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))
        self.patcher = patch('RevealAddressPlugin.QgsCoordinateTransform')
        self.MockTransform = self.patcher.start()
        mock_transform_instance = self.MockTransform.return_value
        mock_transform_instance.transform.side_effect = lambda point: point
        self.tool = RevealAddressMapTool(self.canvas)
        self.tool.coord_transform = mock_transform_instance

    def tearDown(self):
        """
        Sprzątanie po każdym teście.
        """
        self.patcher.stop()
        self.canvas.unsetMapTool(self.tool)

    def test50RandomLocationsInPoland(self):
        with patch('qgis.PyQt.QtWidgets.QMessageBox.information') as mock_msg_box:
            
            for i in range(50):
                lat = random.uniform(MIN_LAT, MAX_LAT)
                lon = random.uniform(MIN_LON, MAX_LON)   
                print(f"Testowanie lokalizacji {i+1}/50: Lat {lat:.4f}, Lon {lon:.4f}")
                mock_event = MagicMock()
                self.tool.toMapCoordinates = MagicMock(return_value=QgsPointXY(lon, lat))
                self.tool.canvasReleaseEvent(mock_event)
                start_time = time.time()
                while not mock_msg_box.called:
                    QgsApplication.processEvents()                  
                    if time.time() - start_time > 15: 
                        self.fail(f"Timeout: Brak odpowiedzi dla lokalizacji {lat}, {lon}")
                    time.sleep(0.01)
                mock_msg_box.reset_mock()
                time.sleep(1.1)

if __name__ == "__main__":
    unittest.main()