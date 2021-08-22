from typing import Dict
import os

from . import ChopperTool
from . import ChopperView

def getMetaData() -> Dict:
    return {
        "tool": {
            "name": "Chop",
            "description": "Chop up model",
            "icon": "cut.svg",
            "tool_panel": "ChopperTool.qml",
            "weight": 4,
            "location": os.path.abspath(os.path.dirname(__file__))
        },
        "view":
        {
            "name": "Chop",
            "view_panel": "",
            "visible": False
        }
    }


def register(app) -> Dict:
    return {"tool": ChopperTool.ChopperTool(),
            "view": ChopperView.ChopperView()}
