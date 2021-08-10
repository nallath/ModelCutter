import QtQuick 2.2
import QtQuick.Controls 1.2

import UM 1.0 as UM


Item
{
    width: childrenRect.width
    height: childrenRect.height
    Column
    {
        Button
        {
            id: cutButton
            text: "Cut object at plane"
            width: 200
            height: 50
            onClicked: UM.ActiveTool.triggerAction("cutObject")
        }

        Label
        {
            text: "Cutting plane direction"
        }
        Row
        {
            height: 50
            Button
            {
                text: "X"
                width: 50
                height: 50
                onClicked: UM.ActiveTool.setProperty("CutDirection", "x")
            }
            Button
            {
                text: "Y"
                width: 50
                height: 50
                onClicked: UM.ActiveTool.setProperty("CutDirection", "y")
            }
            Button
            {
                text: "Z"
                width: 50
                height: 50
                onClicked: UM.ActiveTool.setProperty("CutDirection", "z")
            }
        }
    }
    /*Button
    {
        id: chopButton
        text: "Chop selected models"
        width: 100
        height:100
        onClicked: UM.ActiveTool.setProperty("IsCutting", true)
        Connections
        {
            target: UM.ActiveTool;
            onPropertiesChanged:
            {
                chopButton.visible = !UM.ActiveTool.properties.getValue("IsCutting")
            }
        }
    }*/
}
