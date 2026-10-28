import QtQuick
import QtQuick.Controls as Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
    id: root
    moduleName: "bjl.accent"
    property string serviceState: "unknown"
    property bool autostart: false
    property string error: ""
    property bool menuOpen: false
    property string response: ""
    readonly property bool running: serviceState === "active"
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    function close() { menuOpen = false }
    function request(action) {
        if (control.running) return
        response = ""
        control.command = ["python3", "-B", Qt.resolvedUrl("control.py").toString().replace("file://", ""), action]
        control.running = true
    }
    IpcHandler {
        target: "bjl.accent"
        function status(): string { return JSON.stringify({state: root.serviceState, autostart: root.autostart, error: root.error}) }
        function settings(): void { root.request("settings") }
        function menu(): void { root.menuOpen = !root.menuOpen }
    }
    Process {
        id: control
        stdout: StdioCollector { onStreamFinished: root.response = text }
        onExited: function(code) {
            try {
                var result = JSON.parse(root.response)
                root.error = result.error || ""
                if (result.state !== undefined) root.serviceState = result.state
                if (result.autostart !== undefined) root.autostart = result.autostart
            } catch (e) { root.error = "Could not read Accent service status" }
        }
    }
    Timer {
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.request("status")
    }
    WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: "Á"
        dimmed: !root.running
        tooltipText: "Accent — " + (root.running ? "running" : root.serviceState)
                     + "\nClick: settings · Right-click: controls"
                     + (root.error ? "\n" + root.error : "")
        onPressed: function(mouseButton) {
            if (mouseButton === Qt.RightButton) root.menuOpen = !root.menuOpen
            else if (mouseButton === Qt.LeftButton) root.request("settings")
        }
    }
    KeyboardPanel {
        anchorItem: button
        bar: root.bar
        owner: root
        open: root.menuOpen
        contentWidth: Style.space(250)
        contentHeight: actions.implicitHeight
        focusTarget: actions
        Column {
            id: actions
            width: parent.width
            spacing: Style.space(6)
            Keys.onEscapePressed: root.close()
            Text {
                text: "Accent · " + (root.running ? "Running" : root.serviceState)
                color: Color.foreground
                font.family: Style.font.family
                font.pixelSize: Style.font.body
            }
            Repeater {
                model: [
                    {label: "Settings…", action: "settings"},
                    {label: root.running ? "Pause Accent" : "Start Accent", action: root.running ? "stop" : "start"},
                    {label: "Restart Accent", action: "restart"},
                    {label: root.autostart ? "Disable automatic startup" : "Enable automatic startup", action: root.autostart ? "disable" : "enable"}
                ]
                delegate: Controls.Button {
                    required property var modelData
                    width: actions.width
                    enabled: !control.running
                    text: modelData.label
                    contentItem: Text {
                        text: parent.text
                        color: Color.foreground
                        font.family: Style.font.family
                        font.pixelSize: Style.font.body
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.hovered ? Color.selection : Color.background
                        radius: Style.space(4)
                    }
                    onClicked: { root.request(modelData.action); root.close() }
                }
            }
            Text {
                width: parent.width
                visible: root.error.length > 0
                text: root.error
                wrapMode: Text.Wrap
                color: Color.foreground
            }
        }
    }
}
