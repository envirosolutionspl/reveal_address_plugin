import os

"""Wersja wtyczki"""
PLUGIN_NAME = ''
PLUGIN_VERSION = ''
with open(os.path.join(os.path.dirname(__file__), 'metadata.txt'), 'r') as pluginMetadataFile:
    for line in pluginMetadataFile:
        if line.startswith('name='):
            PLUGIN_NAME = line.split('=')[1].strip()
        elif line.startswith('version='):
            PLUGIN_VERSION = line.split('=')[1].strip()

def classFactory(iface):
    # Load the RevealAddressPlugin class from the RevealAddressPlugin.py file
    from .RevealAddressPlugin import RevealAddressPlugin
    return RevealAddressPlugin(iface)
