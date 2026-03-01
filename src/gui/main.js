const { app, BrowserWindow } = require('electron')

function createWindow() {
    const win = new BrowserWindow({
        width: 320,          // 收紧宽度，减少桌面的“隐形阻挡”区域
        height: 450,         // 收紧高度
        transparent: true,   // 背景全透明
        frame: false,        // 无边框模式
        alwaysOnTop: true,   // 永远置顶，不被其他网页或文件夹挡住
        hasShadow: false,    // 去除系统默认阴影，更加自然
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false // 允许跨域和本地文件读取
        }
    })

    win.loadFile('index.html')
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})