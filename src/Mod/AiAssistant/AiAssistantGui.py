"""
AI Assistant chat window GUI implementation
"""

import os
import json
import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

# Check which Qt binding to use (PySide2 or PySide)
try:
    from PySide2.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
        QPushButton, QSplitter, QLabel, QDockWidget, QComboBox,
        QScrollArea, QFrame, QToolButton, QMenu, QAction
    )
    from PySide2.QtCore import Qt, Signal, QSize
    from PySide2.QtGui import QTextCursor, QFont, QIcon
except ImportError:
    from PySide.QtGui import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
        QPushButton, QSplitter, QLabel, QDockWidget, QComboBox,
        QScrollArea, QFrame, QToolButton, QMenu, QAction,
        QTextCursor, QFont, QIcon
    )
    from PySide.QtCore import Qt, Signal, QSize


# Global variable to store the chat window instance
_chat_window_instance = None


class ToolRegistry:
    """Registry of available CAD tools that can be used by the AI assistant"""
    
    def __init__(self):
        self.tools = {}
        self.register_default_tools()
    
    def register_tool(self, name, description, function, parameters=None):
        """Register a new tool with the registry"""
        if parameters is None:
            parameters = []
        
        self.tools[name] = {
            "name": name,
            "description": description,
            "function": function,
            "parameters": parameters
        }
    
    def get_tool(self, name):
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_all_tools(self):
        """Get all registered tools"""
        return self.tools
    
    def get_tool_descriptions(self):
        """Get descriptions of all tools in a format suitable for an LLM"""
        descriptions = []
        for name, tool in self.tools.items():
            param_desc = ""
            if tool["parameters"]:
                params = []
                for param in tool["parameters"]:
                    params.append(f"{param['name']} ({param['type']}): {param['description']}")
                param_desc = "\nParameters:\n" + "\n".join(params)
            
            descriptions.append(f"Tool: {name}\nDescription: {tool['description']}{param_desc}")
        
        return "\n\n".join(descriptions)
    
    def register_default_tools(self):
        """Register the default set of CAD tools"""
        # Basic document operations
        self.register_tool(
            "create_document",
            "Creates a new FreeCAD document",
            self._create_document,
            [{"name": "name", "type": "string", "description": "Name of the new document"}]
        )
        
        # Basic geometry creation
        self.register_tool(
            "create_box",
            "Creates a box with the specified dimensions",
            self._create_box,
            [
                {"name": "length", "type": "float", "description": "Length of the box"},
                {"name": "width", "type": "float", "description": "Width of the box"},
                {"name": "height", "type": "float", "description": "Height of the box"}
            ]
        )
        
        self.register_tool(
            "create_cylinder",
            "Creates a cylinder with the specified dimensions",
            self._create_cylinder,
            [
                {"name": "radius", "type": "float", "description": "Radius of the cylinder"},
                {"name": "height", "type": "float", "description": "Height of the cylinder"}
            ]
        )
        
        self.register_tool(
            "create_sphere",
            "Creates a sphere with the specified radius",
            self._create_sphere,
            [{"name": "radius", "type": "float", "description": "Radius of the sphere"}]
        )
        
        # Transformation tools
        self.register_tool(
            "move_object",
            "Moves an object by the specified vector",
            self._move_object,
            [
                {"name": "object_name", "type": "string", "description": "Name of the object to move"},
                {"name": "x", "type": "float", "description": "X component of displacement vector"},
                {"name": "y", "type": "float", "description": "Y component of displacement vector"},
                {"name": "z", "type": "float", "description": "Z component of displacement vector"}
            ]
        )
        
        self.register_tool(
            "rotate_object",
            "Rotates an object by the specified angles (in degrees)",
            self._rotate_object,
            [
                {"name": "object_name", "type": "string", "description": "Name of the object to rotate"},
                {"name": "x_angle", "type": "float", "description": "Rotation angle around X axis (degrees)"},
                {"name": "y_angle", "type": "float", "description": "Rotation angle around Y axis (degrees)"},
                {"name": "z_angle", "type": "float", "description": "Rotation angle around Z axis (degrees)"}
            ]
        )
        
        # Boolean operations
        self.register_tool(
            "boolean_union",
            "Performs a boolean union operation between two objects",
            self._boolean_union,
            [
                {"name": "object1_name", "type": "string", "description": "Name of the first object"},
                {"name": "object2_name", "type": "string", "description": "Name of the second object"},
                {"name": "result_name", "type": "string", "description": "Name of the resulting object"}
            ]
        )
        
        self.register_tool(
            "boolean_cut",
            "Performs a boolean cut operation between two objects",
            self._boolean_cut,
            [
                {"name": "base_name", "type": "string", "description": "Name of the base object"},
                {"name": "tool_name", "type": "string", "description": "Name of the tool object to cut with"},
                {"name": "result_name", "type": "string", "description": "Name of the resulting object"}
            ]
        )
        
        # Query tools
        self.register_tool(
            "list_objects",
            "Lists all objects in the active document",
            self._list_objects
        )
        
        self.register_tool(
            "get_object_info",
            "Gets information about a specific object",
            self._get_object_info,
            [{"name": "object_name", "type": "string", "description": "Name of the object"}]
        )
    
    # Tool implementations
    def _create_document(self, name):
        doc = FreeCAD.newDocument(name)
        return f"Created new document: {name}"
    
    def _create_box(self, length, width, height):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        box = doc.addObject("Part::Box", "Box")
        box.Length = length
        box.Width = width
        box.Height = height
        doc.recompute()
        return f"Created box with dimensions {length}x{width}x{height}"
    
    def _create_cylinder(self, radius, height):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        cylinder = doc.addObject("Part::Cylinder", "Cylinder")
        cylinder.Radius = radius
        cylinder.Height = height
        doc.recompute()
        return f"Created cylinder with radius {radius} and height {height}"
    
    def _create_sphere(self, radius):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        sphere = doc.addObject("Part::Sphere", "Sphere")
        sphere.Radius = radius
        doc.recompute()
        return f"Created sphere with radius {radius}"
    
    def _move_object(self, object_name, x, y, z):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        obj = doc.getObject(object_name)
        if not obj:
            return f"Object '{object_name}' not found"
        
        if hasattr(obj, "Placement"):
            placement = obj.Placement
            placement.Base.x += x
            placement.Base.y += y
            placement.Base.z += z
            obj.Placement = placement
            doc.recompute()
            return f"Moved object '{object_name}' by vector ({x}, {y}, {z})"
        else:
            return f"Object '{object_name}' cannot be moved (no Placement property)"
    
    def _rotate_object(self, object_name, x_angle, y_angle, z_angle):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        obj = doc.getObject(object_name)
        if not obj:
            return f"Object '{object_name}' not found"
        
        if hasattr(obj, "Placement"):
            import math
            from FreeCAD import Rotation
            
            # Create rotation
            rotation = Rotation(math.radians(x_angle), 
                               math.radians(y_angle), 
                               math.radians(z_angle))
            
            # Apply rotation to current placement
            placement = obj.Placement
            placement.Rotation = rotation.multiply(placement.Rotation)
            obj.Placement = placement
            
            doc.recompute()
            return f"Rotated object '{object_name}' by angles ({x_angle}, {y_angle}, {z_angle}) degrees"
        else:
            return f"Object '{object_name}' cannot be rotated (no Placement property)"
    
    def _boolean_union(self, object1_name, object2_name, result_name):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        obj1 = doc.getObject(object1_name)
        obj2 = doc.getObject(object2_name)
        
        if not obj1:
            return f"Object '{object1_name}' not found"
        if not obj2:
            return f"Object '{object2_name}' not found"
        
        # Create boolean union
        union = doc.addObject("Part::Fuse", result_name)
        union.Base = obj1
        union.Tool = obj2
        doc.recompute()
        
        return f"Created boolean union '{result_name}' from '{object1_name}' and '{object2_name}'"
    
    def _boolean_cut(self, base_name, tool_name, result_name):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        base = doc.getObject(base_name)
        tool = doc.getObject(tool_name)
        
        if not base:
            return f"Object '{base_name}' not found"
        if not tool:
            return f"Object '{tool_name}' not found"
        
        # Create boolean cut
        cut = doc.addObject("Part::Cut", result_name)
        cut.Base = base
        cut.Tool = tool
        doc.recompute()
        
        return f"Created boolean cut '{result_name}' by cutting '{tool_name}' from '{base_name}'"
    
    def _list_objects(self):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        objects = []
        
        for obj in doc.Objects:
            obj_type = obj.TypeId.split("::")[1] if "::" in obj.TypeId else obj.TypeId
            objects.append(f"{obj.Name}: {obj_type}")
        
        if not objects:
            return "No objects in the active document."
        
        return "Objects in the active document:\n" + "\n".join(objects)
    
    def _get_object_info(self, object_name):
        if not FreeCAD.ActiveDocument:
            return "No active document. Please create a document first."
        
        doc = FreeCAD.ActiveDocument
        obj = doc.getObject(object_name)
        
        if not obj:
            return f"Object '{object_name}' not found"
        
        info = [f"Object: {obj.Name}", f"Type: {obj.TypeId}"]
        
        # Add properties
        props = []
        for prop in obj.PropertiesList:
            try:
                value = getattr(obj, prop)
                if hasattr(value, "__module__") and "FreeCAD" in value.__module__:
                    # For FreeCAD specific types, just show type name
                    props.append(f"{prop}: <{type(value).__name__}>")
                else:
                    # For simple types, show the value
                    props.append(f"{prop}: {value}")
            except:
                props.append(f"{prop}: <error reading value>")
        
        info.append("Properties:")
        info.extend(props)
        
        return "\n".join(info)


class LLMConnector:
    """Connector for Large Language Models"""
    
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.model_name = model_name
        self.api_key = None
        self.base_url = None
        self.tool_registry = ToolRegistry()
        self.system_prompt = self._generate_system_prompt()
        self.conversation_history = []
    
    def _generate_system_prompt(self):
        """Generate the system prompt with tool descriptions"""
        tools_description = self.tool_registry.get_tool_descriptions()
        
        return f"""You are an AI assistant for CAD design using FreeCAD. 
You can help users create and modify 3D models by understanding their requirements and using the available CAD tools.

You have access to the following tools that allow you to interact with FreeCAD:

{tools_description}

When a user asks you to perform an action, you should:
1. Understand the user's intent
2. Choose the appropriate tool(s) for the task
3. Call the tool(s) with the right parameters
4. Explain what you've done in clear language
5. Suggest next steps if applicable

Be precise with measurements and follow the user's specifications exactly.
Always respond in a helpful, informative manner.
"""
    
    def set_api_key(self, api_key):
        """Set the API key for the LLM service"""
        self.api_key = api_key
    
    def set_base_url(self, base_url):
        """Set the base URL for the LLM service"""
        self.base_url = base_url
    
    def set_model(self, model_name):
        """Set the model name to use"""
        self.model_name = model_name
        
    def add_message(self, role, content):
        """Add a message to the conversation history"""
        self.conversation_history.append({"role": role, "content": content})
    
    def send_message(self, message, callback=None):
        """Send a message to the LLM and get a response"""
        # Add user message to history
        self.add_message("user", message)
        
        try:
            # Check for API key
            if not self.api_key:
                # Try to use environmental variable
                import os
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if api_key:
                    self.api_key = api_key
                else:
                    return "API key for the AI service is not set. Please set it in the settings."
            
            # Import API client
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                return "OpenAI Python package is not installed. Please install it with: pip install openai"
            
            # Prepare messages
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            
            # Send request to API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract response
            reply = response.choices[0].message.content
            
            # Add assistant response to history
            self.add_message("assistant", reply)
            
            # Check for tool calls in the response
            tool_calls = self._extract_tool_calls(reply)
            
            if tool_calls:
                # Execute tool calls and get results
                tool_results = []
                for call in tool_calls:
                    result = self._execute_tool_call(call)
                    tool_results.append(result)
                
                # Add function calling results to the conversation
                self.add_message("function", "\n".join(tool_results))
                
                # Get a follow-up response that incorporates the tool results
                followup_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages + [
                        {"role": "assistant", "content": reply},
                        {"role": "function", "content": "\n".join(tool_results)}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                # Extract and return the followup response
                followup_reply = followup_response.choices[0].message.content
                self.add_message("assistant", followup_reply)
                
                return reply + "\n\n" + "\n".join(tool_results) + "\n\n" + followup_reply
            
            return reply
            
        except Exception as e:
            import traceback
            error_message = f"Error communicating with AI service: {str(e)}\n{traceback.format_exc()}"
            FreeCAD.Console.PrintError(error_message + "\n")
            return f"Error: {str(e)}"
    
    def _extract_tool_calls(self, text):
        """Extract tool calls from the response text"""
        tool_calls = []
        
        # Look for patterns like "use_tool(param1, param2)"
        import re
        pattern = r'(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            tool_name = match[0]
            params_str = match[1]
            
            # Check if the tool exists
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                # Parse parameters
                params = []
                if params_str.strip():
                    # Split by comma, but handle quotes correctly
                    import shlex
                    try:
                        params = [param.strip().strip('\'"') for param in shlex.split(params_str, posix=False, comments=False)]
                    except:
                        # Fallback to simpler splitting if shlex fails
                        params = [param.strip().strip('\'"') for param in params_str.split(',')]
                
                tool_calls.append({
                    "name": tool_name,
                    "parameters": params
                })
        
        return tool_calls
    
    def _execute_tool_call(self, call):
        """Execute a tool call and return the result"""
        tool_name = call["name"]
        params = call["parameters"]
        
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            # Convert parameters to the right types
            converted_params = []
            expected_params = tool.get("parameters", [])
            
            # If there are more parameters than expected, ignore extras
            for i, param in enumerate(params):
                if i >= len(expected_params):
                    break
                
                param_type = expected_params[i]["type"]
                if param_type == "float":
                    converted_params.append(float(param))
                elif param_type == "int":
                    converted_params.append(int(param))
                else:
                    converted_params.append(param)
            
            # Execute the function
            result = tool["function"](*converted_params)
            return f"Tool '{tool_name}' executed: {result}"
            
        except Exception as e:
            import traceback
            error_message = f"Error executing tool '{tool_name}': {str(e)}\n{traceback.format_exc()}"
            FreeCAD.Console.PrintError(error_message + "\n")
            return f"Error executing tool '{tool_name}': {str(e)}"


class ChatMessageWidget(QWidget):
    """Widget for displaying a single chat message"""
    
    def __init__(self, text, sender_type="user", parent=None):
        super(ChatMessageWidget, self).__init__(parent)
        self.text = text
        self.sender_type = sender_type
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Message frame
        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        
        # Color based on sender type
        if self.sender_type == "user":
            frame.setStyleSheet("background-color: #E9F5FE; border-radius: 5px;")
        else:
            frame.setStyleSheet("background-color: #F0F0F0; border-radius: 5px;")
        
        # Message layout
        msg_layout = QVBoxLayout(frame)
        
        # Header with icon and sender name
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        if self.sender_type == "user":
            icon_label.setText("User:")
            icon_label.setStyleSheet("font-weight: bold; color: #2979FF;")
        else:
            icon_label.setText("AI Assistant:")
            icon_label.setStyleSheet("font-weight: bold; color: #43A047;")
        
        header_layout.addWidget(icon_label)
        header_layout.addStretch(1)
        
        # Add timestamp
        import datetime
        timestamp = QLabel(datetime.datetime.now().strftime("%H:%M"))
        timestamp.setStyleSheet("color: #757575; font-size: 9pt;")
        header_layout.addWidget(timestamp)
        
        msg_layout.addLayout(header_layout)
        
        # Message text
        text_label = QLabel(self.text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        text_label.setOpenExternalLinks(True)
        
        msg_layout.addWidget(text_label)
        
        layout.addWidget(frame)


class ChatWindow(QDockWidget):
    """The main chat window widget that integrates with FreeCAD"""
    
    def __init__(self, parent=None):
        super(ChatWindow, self).__init__(parent)
        
        self.setWindowTitle("AI Assistant")
        self.setObjectName("AiAssistantDockWidget")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Create the LLM connector
        self.llm_connector = LLMConnector()
        
        # Set up the UI
        self.setup_ui()
        
        # Create welcome message
        welcome_text = """Welcome to the AI Assistant! 
I can help you create and modify 3D models in FreeCAD.
Ask me to create shapes, modify objects, or perform operations.

For example:
- "Create a box with dimensions 10x20x30"
- "Move the box by 5 units in the X direction"
- "Cut a cylinder from the box"

How can I help you today?"""
        
        self.add_message(welcome_text, "assistant")
    
    def setup_ui(self):
        # Main widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Settings section
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_frame.setFrameShadow(QFrame.Raised)
        settings_layout = QHBoxLayout(settings_frame)
        
        # Model selection
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "claude-3-opus"])
        self.model_combo.setCurrentText("gpt-3.5-turbo")
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        
        # API Key button
        self.api_key_button = QPushButton("Set API Key")
        self.api_key_button.clicked.connect(self.on_set_api_key)
        
        settings_layout.addWidget(model_label)
        settings_layout.addWidget(self.model_combo)
        settings_layout.addWidget(self.api_key_button)
        settings_layout.addStretch(1)
        
        main_layout.addWidget(settings_frame)
        
        # Chat messages area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(10)
        
        self.chat_scroll.setWidget(self.chat_container)
        main_layout.addWidget(self.chat_scroll, 1)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setAcceptRichText(False)
        self.message_input.setMaximumHeight(80)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.on_send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        
        main_layout.addLayout(input_layout)
        
        # Set up keyboard shortcut for sending messages
        self.send_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self.message_input)
        self.send_shortcut.activated.connect(self.on_send_message)
    
    def on_model_changed(self, model_name):
        """Handle model selection change"""
        self.llm_connector.set_model(model_name)
    
    def on_set_api_key(self):
        """Handle API key button click"""
        from PySide import QtGui
        
        api_key, ok = QtGui.QInputDialog.getText(
            self, "API Key", "Enter your API key:",
            QtGui.QLineEdit.Password
        )
        
        if ok and api_key:
            self.llm_connector.set_api_key(api_key)
            QtGui.QMessageBox.information(self, "API Key", "API key has been set successfully.")
        elif ok:
            QtGui.QMessageBox.warning(self, "API Key", "No API key provided.")
    
    def on_send_message(self):
        """Handle send button click"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        
        # Clear input
        self.message_input.clear()
        
        # Add user message to chat
        self.add_message(message, "user")
        
        # Show thinking indicator
        thinking_widget = ChatMessageWidget("Thinking...", "assistant")
        self.chat_layout.addWidget(thinking_widget)
        self.scroll_to_bottom()
        
        # Process with LLM in a separate thread to avoid blocking the UI
        def process_message():
            response = self.llm_connector.send_message(message)
            
            # Update UI in the main thread
            def update_ui():
                # Remove thinking indicator
                thinking_widget.setParent(None)
                thinking_widget.deleteLater()
                
                # Add response
                self.add_message(response, "assistant")
            
            from PySide import QtCore
            QtCore.QMetaObject.invokeMethod(self, "update_ui", QtCore.Qt.QueuedConnection)
        
        # Run in a separate thread
        import threading
        thread = threading.Thread(target=process_message)
        thread.daemon = True
        thread.start()
    
    @QtCore.Slot()
    def update_ui(self):
        """Update UI after message processing"""
        pass  # Actual implementation in process_message
    
    def add_message(self, text, sender_type):
        """Add a message to the chat"""
        # Create message widget
        message_widget = ChatMessageWidget(text, sender_type)
        self.chat_layout.addWidget(message_widget)
        
        # Scroll to bottom
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll the chat to the bottom"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class OpenChatCommand:
    """Command to open the AI Assistant chat window"""
    
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "Resources", "icons", "AiAssistant.svg"),
            'MenuText': "AI Assistant Chat",
            'ToolTip': "Open the AI Assistant chat window"
        }
    
    def Activated(self):
        showChatWindow()
        return
    
    def IsActive(self):
        return True


# Register the command
FreeCADGui.addCommand("AiAssistant_OpenChat", OpenChatCommand())


def showChatWindow():
    """Show the AI Assistant chat window"""
    global _chat_window_instance
    
    # Check if an instance already exists
    if _chat_window_instance is None:
        # Create a new instance
        main_window = FreeCADGui.getMainWindow()
        _chat_window_instance = ChatWindow(main_window)
        main_window.addDockWidget(Qt.RightDockWidgetArea, _chat_window_instance)
    
    # Make sure the window is visible
    _chat_window_instance.setVisible(True)
    _chat_window_instance.raise_()
    
    return _chat_window_instance 