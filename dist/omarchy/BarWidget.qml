import QtQuick
import QtQuick.Controls as Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Theme.js" as AccentTheme

BarWidget {
    id: root
    moduleName: "bjl.accent"
    property string serviceState: "unknown"
    property bool autostart: false
    property string error: ""
    property bool menuOpen: false
    property string response: ""
    property string themeId: "aurora-glass"
    readonly property bool systemTheme: themeId === "system"
    FileView {
        path: Quickshell.env("HOME") + "/.config/accent/config.toml"
        watchChanges: true
        printErrors: false
        onLoaded: root.themeId = AccentTheme.fromConfig(text())
        onFileChanged: reload()
    }
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
        function status(): string { return JSON.stringify({state: root.serviceState, autostart: root.autostart, theme: root.themeId, error: root.error}) }
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
        text: ""
        labelVisible: false
        hasVisualContent: true
        fixedWidth: root.vertical ? root.barSize : Style.bar.iconSlot
        fixedHeight: root.vertical ? Style.bar.iconSlot : root.barSize
        readonly property real badgeSize: Math.max(12, Math.min(Style.space(24), root.barSize - Style.space(6)))
        Image {
            anchors.centerIn: parent
            width: button.badgeSize
            height: width
            visible: !root.systemTheme
            source: visible ? Qt.resolvedUrl("assets/themes/" + root.themeId + ".svg") : ""
            sourceSize.width: Math.ceil(width * 2)
            sourceSize.height: Math.ceil(height * 2)
            fillMode: Image.PreserveAspectFit
            smooth: true
            scale: button.pressScale
        }
        Rectangle {
            anchors.centerIn: parent
            width: button.badgeSize * 0.91
            height: width
            visible: root.systemTheme
            radius: width * 0.21
            color: Color.background
            border.color: Color.accent
            border.width: 1
            scale: button.pressScale
            Text {
                anchors.centerIn: parent
                textFormat: Text.PlainText
                text: "Á"
                font.family: Style.font.family
                font.pixelSize: parent.height * 0.78
                font.bold: true
                color: Color.foreground
            }
        }
        dimmed: !root.running
        tooltipText: "Accent — " + (root.running ? "running" : AccentTheme.plain(root.serviceState))
                     + "\nClick: settings · Right-click: controls"
                     + (root.error ? "\n" + AccentTheme.plain(root.error) : "")
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
                textFormat: Text.PlainText
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
                        textFormat: Text.PlainText
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
                textFormat: Text.PlainText
                width: parent.width
                visible: root.error.length > 0
                text: root.error
                wrapMode: Text.Wrap
                color: Color.foreground
            }
        }
    }
}
