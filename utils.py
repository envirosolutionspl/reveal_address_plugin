from qgis._core import QgsMessageLog, Qgis
from . import PLUGIN_NAME

class QgsTools:
    default_tag = PLUGIN_NAME

    @staticmethod
    def pushLogInfo(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Info)

    @staticmethod
    def pushLogWarning(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Warning)

    @staticmethod
    def pushLogCritical(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Critical)
