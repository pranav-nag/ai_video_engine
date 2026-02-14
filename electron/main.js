const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;

// PY_DIST_FOLDER = 'dist-python' (for future usage)
// PY_FOLDER = 'backend'
// PY_MODULE = 'api.py'

const isDev = !app.isPackaged;

function getPythonPath() {
    let pythonPath;
    if (isDev) {
        // In Development: Use relative path to .venv
        pythonPath = path.join(__dirname, '../.venv/Scripts/python.exe');
    } else {
        // In Production: .venv is usually in resources folder
        pythonPath = path.join(process.resourcesPath, '.venv/Scripts/python.exe');
        
        // Fast Build Fallback: If .venv wasn't copied, look in the project root relative to the exe
        if (!fs.existsSync(pythonPath)) {
            // Unpacked exe is in dist/win-unpacked/resources/app.asar
            // Root .venv is 5 levels up: ../../../../../.venv
            const fallbackPath = path.resolve(__dirname, '../../../../../.venv/Scripts/python.exe');
            if (fs.existsSync(fallbackPath)) {
                pythonPath = fallbackPath;
            }
        }
    }

    if (fs.existsSync(pythonPath)) {
        console.log(`✅ Found Python: ${pythonPath}`);
        return pythonPath;
    }
    
    console.error(`❌ Python not found at: ${pythonPath}`);
    return 'python'; // Fallback
}

function createPythonProcess() {
    const pythonPath = getPythonPath();
    let scriptPath = isDev 
        ? path.join(__dirname, '../backend/api.py')
        : path.join(process.resourcesPath, 'backend/api.py');
    
    let cwd = isDev ? path.join(__dirname, '..') : process.resourcesPath;

    // Fast Build Fallback: If backend is not in resources, use project root
    if (!isDev && !fs.existsSync(scriptPath)) {
        const fallbackScript = path.resolve(__dirname, '../../../../../backend/api.py');
        if (fs.existsSync(fallbackScript)) {
            scriptPath = fallbackScript;
            cwd = path.resolve(__dirname, '../../../../..');
        }
    }
    
    console.log(`🚀 Spawning Python Backend: ${pythonPath} ${scriptPath}`);

    // WINDOWS ONLY: Spawn in a new visible console window
    // "start" command opens a new window. 
    // "/wait" makes the spawn command wait for the window to close (optional, but good for tracking)
    // "AI Engine Backend" is the window title
    const command = `start "AI Engine Backend" /wait "${pythonPath}" "${scriptPath}"`;

    // Use shell: true to execute the command string
    pythonProcess = spawn(command, {
        cwd: cwd,
        shell: true, 
        detached: false 
    });

    pythonProcess.on('close', (code) => {
        console.log(`[Python]: Exited with code ${code}`);
    });
    
    // Note: When spawning via 'start', we lose direct stdout/stderr access in the parent 
    // because it's in a new window. The user will see logs in that new window.
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 850,
        frame: true, // Use system frame for minimize/close/maximize
        resizable: true, // Allow resizing
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        }
    });

    if (isDev) {
        mainWindow.loadURL('http://localhost:5173'); // Vite Dev Server
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, 'frontend/dist/index.html'));
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.on('ready', () => {
    createPythonProcess();
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
        console.log('💀 Killed Python Process');
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

// IPC Handlers
ipcMain.on('open-folder', (event, folderPath) => {
    shell.openPath(folderPath);
});

ipcMain.on('open-file', (event, filePath) => {
    shell.openPath(filePath);
});
