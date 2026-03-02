const { app, BrowserWindow, ipcMain } = require('electron')

function createWindow() {
    const win = new BrowserWindow({
        width: 600,
        height: 520,
        transparent: true,
        frame: false,
        alwaysOnTop: true,
        hasShadow: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false
        }
    })

    win.loadFile('index.html')

    // NOTE: 手动实现窗口拖拽，替代 -webkit-app-region: drag
    // 因为 drag 会吞掉所有鼠标事件，导致 click 无法触发
    ipcMain.on('window-drag', (event, { dx, dy }) => {
        const [x, y] = win.getPosition()
        win.setPosition(x + dx, y + dy)
    })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})