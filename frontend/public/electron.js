const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

let mainWindow;
let backendProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // Load the frontend
    if (app.isPackaged) {
        // In production, load the built React app
        mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
    } else {
        // In development, load from localhost
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', function () {
        mainWindow = null;
        if (backendProcess) {
            console.log('Killing backend process...');
            backendProcess.kill();
        }
    });
}

function waitForBackend(url, callback, maxAttempts = 30) {
    let attempts = 0;
    const check = () => {
        attempts++;
        http.get(url, (res) => {
            if (res.statusCode === 200) {
                console.log('Backend is ready!');
                callback();
            } else {
                retry();
            }
        }).on('error', (err) => {
            console.log(`Waiting for backend... Attempt ${attempts}/${maxAttempts}`);
            retry();
        });
    };

    const retry = () => {
        if (attempts < maxAttempts) {
            setTimeout(check, 1000);
        } else {
            console.error('Backend failed to start after maximum attempts');
            // Show error dialog
            const { dialog } = require('electron');
            dialog.showErrorBox('Backend Error',
                'Failed to start the backend server. Please check if antivirus is blocking the application.');
            createWindow();
        }
    };

    check();
}

function startBackend() {
    let backendPath;
    let backendCwd;
    let backendCommand;
    let backendArgs = [];

    if (app.isPackaged) {
        // In packaged app, use the bundled exe
        if (process.platform === 'win32') {
            // Windows: Use the .exe file
            backendPath = path.join(process.resourcesPath, 'app', 'delta-backend.exe');
            backendCommand = backendPath;

            // Check if exe exists
            if (!fs.existsSync(backendPath)) {
                console.error('Backend executable not found at:', backendPath);
                // Try alternative path
                backendPath = path.join(process.resourcesPath, 'delta-backend.exe');
                backendCommand = backendPath;
            }
        } else {
            // Mac/Linux: Use the bundled Python
            backendPath = path.join(process.resourcesPath, 'app', 'delta-backend');
            backendCommand = backendPath;
        }
        backendCwd = path.join(process.resourcesPath, 'app');

        console.log('Using bundled backend at:', backendPath);
    } else {
        // In development, use Python directly
        backendCommand = process.platform === 'win32' ? 'python' : 'python3';
        backendPath = path.join(__dirname, '../../app.py');
        backendArgs = [backendPath];
        backendCwd = path.join(__dirname, '../..');

        console.log('Using Python backend at:', backendPath);
    }

    console.log('Backend command:', backendCommand);
    console.log('Backend args:', backendArgs);
    console.log('Backend CWD:', backendCwd);

    // Ensure the working directory exists
    if (!fs.existsSync(backendCwd)) {
        console.log('Creating backend directory:', backendCwd);
        fs.mkdirSync(backendCwd, { recursive: true });
    }

    // Copy database to user data directory if it doesn't exist (for packaged app)
    if (app.isPackaged) {
        const userDataPath = app.getPath('userData');
        const userDbPath = path.join(userDataPath, 'database.db');
        const sourceDbPath = path.join(process.resourcesPath, 'app', 'database.db');

        if (!fs.existsSync(userDbPath) && fs.existsSync(sourceDbPath)) {
            console.log('Copying database to user directory...');
            fs.copyFileSync(sourceDbPath, userDbPath);
        }

        // Set environment variable for database path
        process.env.DATABASE_PATH = userDbPath;
    }

    // Start backend
    try {
        backendProcess = spawn(backendCommand, backendArgs, {
            cwd: backendCwd,
            stdio: app.isPackaged ? 'ignore' : 'inherit',  // Hide console in production
            windowsHide: true,  // Hide console window on Windows
            env: {
                ...process.env,
                FLASK_APP: 'app.py',
                FLASK_ENV: app.isPackaged ? 'production' : 'development',
                DATABASE_PATH: process.env.DATABASE_PATH || path.join(backendCwd, 'database.db')
            },
            detached: process.platform !== 'win32',  // Detach process on Unix
            shell: false  // Don't use shell to avoid console window
        });

        backendProcess.on('error', (err) => {
            console.error('Failed to start backend:', err);
            const { dialog } = require('electron');
            dialog.showErrorBox('Backend Error',
                `Failed to start backend server: ${err.message}\n\nPlease make sure antivirus is not blocking the application.`);
            createWindow();
        });

        backendProcess.on('exit', (code) => {
            console.log(`Backend process exited with code ${code}`);
            if (code !== 0 && code !== null) {
                const { dialog } = require('electron');
                dialog.showErrorBox('Backend Crashed',
                    'The backend server crashed. Please restart the application.');
            }
        });

        // Wait for backend to be ready
        waitForBackend('http://127.0.0.1:5000', () => {
            createWindow();
        });
    } catch (error) {
        console.error('Error spawning backend:', error);
        const { dialog } = require('electron');
        dialog.showErrorBox('Startup Error',
            `Failed to start application: ${error.message}`);
        createWindow();
    }
}

app.whenReady().then(() => {
    startBackend();
});

app.on('window-all-closed', function () {
    if (backendProcess) {
        backendProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});

// Cleanup on app quit
app.on('before-quit', () => {
    if (backendProcess) {
        console.log('Terminating backend process...');
        if (process.platform === 'win32') {
            spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
        } else {
            backendProcess.kill();
        }
    }
});