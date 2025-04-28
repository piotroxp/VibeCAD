"""
Initialize the AiAssistant module for FreeCAD
"""

import FreeCAD
import os

FreeCAD.addImportType("AI Assistant (*.json)", "AiAssistantImport")

# Get the module path
mod_path = os.path.dirname(__file__)
icon_path = os.path.join(mod_path, "Resources", "icons")

# Register the icon path
if os.path.exists(icon_path):
    FreeCAD.addIconPath(icon_path) 