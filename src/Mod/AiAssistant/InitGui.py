"""Initialize the AI Assistant workbench GUI"""

import os
import FreeCAD
import FreeCADGui

class AiAssistantWorkbench(FreeCADGui.Workbench):
    """The AI Assistant Workbench that provides the chat interface"""
    
    MenuText = "AI Assistant"
    ToolTip = "AI Assistant for CAD design"
    Icon = """
/* XPM */
static char * ai_assistant_icon_xpm[] = {
"16 16 4 1",
" 	c None",
".	c #3465A4",
"+	c #204A87",
"@	c #729FCF",
"    ........    ",
"   ..++++++..   ",
"  .+++++++++++. ",
" .++++++++++++++.",
" .+@@@+++++++@++.",
".+@@@@+++++++@@+.",
".+@@@@+++++++@@+.",
".+@@@@+++++++@@+.",
".+@@@@+++++++@@+.",
".+@@@@+++++++@@+.",
".+@@@@+++++++@@+.",
" .+@@@+++++++@++.",
" .++++++++++++++.",
"  .+++++++++++. ",
"   ..++++++..   ",
"    ........    "};
"""
    
    def __init__(self):
        self.__class__.Icon = self.getIcon()
    
    def getIcon(self):
        # Try to get a custom icon if available
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "Resources", "icons", "AiAssistant.svg")
            if os.path.exists(icon_path):
                return icon_path
            return self.Icon
        except:
            return self.Icon
    
    def Initialize(self):
        """Called when the workbench is first activated"""
        import AiAssistantGui
        
        # Create commands
        self.chat_command = AiAssistantGui.OpenChatCommand()
        
        # Create menu and toolbar
        self.appendToolbar("AI Assistant", ["AiAssistant_OpenChat"])
        self.appendMenu("AI Assistant", ["AiAssistant_OpenChat"])

    def Activated(self):
        """Called when the workbench is activated"""
        if FreeCAD.GuiUp:
            from PySide import QtCore
            QtCore.QTimer.singleShot(500, self.showDockWindow)
        return True
    
    def showDockWindow(self):
        """Show the AI assistant chat window automatically"""
        import AiAssistantGui
        AiAssistantGui.showChatWindow()
    
    def Deactivated(self):
        """Called when the workbench is deactivated"""
        return True
    
    def GetClassName(self):
        """Return the name of the class"""
        return "Gui::PythonWorkbench"

# Add the workbench to the list of workbenches
FreeCADGui.addWorkbench(AiAssistantWorkbench()) 