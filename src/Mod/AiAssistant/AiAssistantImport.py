"""
Import script for AI Assistant settings and conversations
"""

import os
import json
import FreeCAD

def open(filename):
    """Open an AI Assistant settings or conversation file"""
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if 'conversation' in data:
            # Load conversation data
            FreeCAD.Console.PrintMessage(f"Loaded AI Assistant conversation from {filename}\n")
            
            # If GUI is available, open the chat window and load the conversation
            if FreeCAD.GuiUp:
                import AiAssistantGui
                chat_window = AiAssistantGui.showChatWindow()
                
                # TODO: Implement conversation loading in the chat window
                
            return True
            
        elif 'settings' in data:
            # Load settings data
            FreeCAD.Console.PrintMessage(f"Loaded AI Assistant settings from {filename}\n")
            
            # If GUI is available, open the chat window and apply settings
            if FreeCAD.GuiUp:
                import AiAssistantGui
                chat_window = AiAssistantGui.showChatWindow()
                
                # TODO: Implement settings loading in the chat window
                
            return True
            
        else:
            FreeCAD.Console.PrintError(f"Unknown AI Assistant file format in {filename}\n")
            return False
            
    except Exception as e:
        FreeCAD.Console.PrintError(f"Error opening AI Assistant file {filename}: {str(e)}\n")
        return False 