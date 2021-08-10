from typing import Dict


from . import ChopperTool
from . import ChopperView

def getMetaData() -> Dict:
    workspace_extension = "3mf"
    return {
        "tool": {
            "name": "Chop",
            "description": "Chop up model",
            "icon": "",
            "tool_panel": "ChopperTool.qml",
            "weight": 4
        },
        "view":
        {
            "name": "Chop",
            "view_panel": "",
            "visible": False
        }
    }


def register(app) -> Dict:
        return {"tool": ChopperTool.ChopperTool(), "view": ChopperView.ChopperView()}
