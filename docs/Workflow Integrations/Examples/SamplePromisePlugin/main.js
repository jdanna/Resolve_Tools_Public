// NOTE: Follow the security guide while implementing plugin app https://www.electronjs.org/docs/tutorial/security

// Modules to control application life and create native browser window.
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const WorkflowIntegration = require('./WorkflowIntegration.node')

const PLUGIN_ID = 'com.blackmagicdesign.resolve.samplepromiseplugin';

// Cached objects
let initObj = null;
let resolvePromiseObj = null;

// Function to log into renderer window console.
function debugLog(message) {
    mainWindow.webContents.executeJavaScript("console.log('%cMAIN:', 'color: #800', '" + message + "');");
}

// Initialize and return interface object (cached object internally).
async function initialize() {
    if (!initObj) {
        // Initialize workflow interface
        initObj = await WorkflowIntegration.InitializePromise(PLUGIN_ID); // wait for the response to avoid multiple async calls in parallel
        if (!initObj) {
            debugLog('Error: Failed to initialize!');
        }
    }

    return initObj;
}

// Cleanup Resolve interface.
async function cleanupResolveInterface() {
    WorkflowIntegration.CleanUp(); // blocking api call

    initObj = null;
    resolvePromiseObj = null;
}

// Gets Resolve promise object (cached object internally).
async function getResolvePromise() {
    // Return cached resolve promise object
    if (resolvePromiseObj) return resolvePromiseObj;

    if (!initObj) {
        if (!await initialize()) {
            return null;
        }
    }

    resolvePromiseObj = WorkflowIntegration.GetResolvePromise();
    return resolvePromiseObj;
}

// Opens input page.
async function openPage(event, pageName) {

    resolve = await getResolvePromise();
    if (!resolve) return null;

    return await resolve.OpenPage(pageName);
}

// Creates a new project.
function createProject(event, projectName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.CreateProject(projectName).then(
                        function (newProject) {
                            debugLog(`Created project: ${projectName}`);
                        },
                        function (error) {
                            debugLog(`Error: Failed to create project: ${projectName}, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Saves current project.
function saveProject() {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.SaveProject().then(
                        function (result) {
                            debugLog(`Saved project`);
                        },
                        function (error) {
                            debugLog(`Error: Failed to save project: ${projectName}, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Opens a project.
function openProject(event, projName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.LoadProject(projName).then(
                        function (project) {
                            debugLog(`Opened project: ${projName}`);
                        },
                        function (error) {
                            debugLog(`Error: Failed to open project: ${projName}, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to get resolve object, ${error}`);
        }
    );
}

// Creates a new bin.
function createBin(event, binName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.GetCurrentProject().then(
                        function (currentProjectValue) {
                            currentProjectValue.GetMediaPool().then(
                                function (mediaPoolValue) {
                                    mediaPoolValue.GetRootFolder().then(
                                        function (rootFolderValue) {
                                            mediaPoolValue.AddSubFolder(rootFolderValue, binName).then(
                                                function (folder) {
                                                    debugLog(`Created bin: ${binName}`);
                                                },
                                                function (error) {
                                                    debugLog(`Error: Failed to create bin: ${binName}, ${error}`);
                                                }
                                            );
                                        },
                                        function (error) {
                                            debugLog(`Error: Failed to get root bin object, ${error}`);
                                        }
                                    );
                                },
                                function (error) {
                                    debugLog(`Error: Failed to get media pool object, ${error}`);
                                }
                            );
                        },
                        function (error) {
                            debugLog(`Error: Failed to get current project object, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Selects first matching bin with input name.
function selectBin(event, binName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.GetCurrentProject().then(
                        function (currentProjectValue) {
                            currentProjectValue.GetMediaPool().then(
                                function (mediaPoolValue) {
                                    mediaPoolValue.GetRootFolder().then(
                                        function (rootFolderValue) {
                                            rootFolderValue.GetSubFolderList().then(
                                                function (folderListValue) {
                                                    if (!folderListValue || (folderListValue.length === 0)) {
                                                        debugLog(`Error: Failed to get root folder list`);
                                                        return;
                                                    }

                                                    isDone = false;
                                                    for (const folder of folderListValue) {
                                                        if (isDone) return;
                                                        folder.GetName().then(
                                                            function (folderNameValue) {
                                                                if (isDone) return;
                                                                if (folderNameValue === binName) {
                                                                    mediaPoolValue.SetCurrentFolder(folder).then(
                                                                        function (value) {
                                                                            debugLog(`Selected bin: ${binName}`);
                                                                        },
                                                                        function (error) {
                                                                            debugLog(`Error: Failed to select bin: ${binName}, ${error}`);
                                                                        }
                                                                    );

                                                                    isDone = true;
                                                                    return;
                                                                }
                                                            },
                                                            function (error) {
                                                                // ignore
                                                            }
                                                        );
                                                    }
                                                },
                                                function (error) {
                                                    debugLog(`Error: Failed to get folder list, ${error}`);
                                                }
                                            );
                                        },
                                        function (error) {
                                            debugLog(`Error: Failed to get root bin object, ${error}`);
                                        }
                                    );
                                },
                                function (error) {
                                    debugLog(`Error: Failed to get media pool object, ${error}`);
                                }
                            );
                        },
                        function (error) {
                            debugLog(`Error: Failed to get curret project object, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Deletes first matching bin using name.
function deleteBin(event, binName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.GetCurrentProject().then(
                        function (currentProjectValue) {
                            currentProjectValue.GetMediaPool().then(
                                function (mediaPoolValue) {
                                    mediaPoolValue.GetRootFolder().then(
                                        function (rootFolderValue) {
                                            rootFolderValue.GetSubFolderList().then(
                                                function (folderListValue) {
                                                    if (!folderListValue || (folderListValue.length === 0)) {
                                                        debugLog(`Error: Failed to get root folder list`);
                                                        return;
                                                    }

                                                    isDone = false;
                                                    for (const folder of folderListValue) {
                                                        if (isDone) return;
                                                        folder.GetName().then(
                                                            function (folderNameValue) {
                                                                if (isDone) return;
                                                                if (folderNameValue && (folderNameValue === binName)) {
                                                                    const folderToDeleteList = [folder];
                                                                    mediaPoolValue.DeleteFolders(folderToDeleteList).then(
                                                                        function (value) {
                                                                            debugLog(`Deleted bin: ${binName}`);
                                                                        },
                                                                        function (error) {
                                                                            debugLog(`Error: Failed to delete bin: ${binName}, ${error}`);
                                                                        }
                                                                    );

                                                                    isDone = true;
                                                                    return;
                                                                }
                                                            },
                                                            function (error) {
                                                                // ignore
                                                            }
                                                        );
                                                    }
                                                },
                                                function (error) {
                                                    debugLog(`Error: Failed to get folder list, ${error}`);
                                                }
                                            );
                                        },
                                        function (error) {
                                            debugLog(`Error: Failed to get root bin object, ${error}`);
                                        }
                                    );
                                },
                                function (error) {
                                    debugLog(`Error: Failed to get media pool object, ${error}`);
                                }
                            );
                        },
                        function (error) {
                            debugLog(`Error: Failed to get curret project object, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Select clips to be added to media pool.
async function selectClipsToAdd() {
    const result = await dialog.showOpenDialog({
        title: 'Select Media Files',
        buttonLabel: 'Select',
        properties: ['openFile', 'multiSelections']
    });

    return result.canceled ? [] : result.filePaths;
}

// Add clips to media pool.
function addClips(event, filePathsArray) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetMediaStorage().then(
                function (mediaStorageValue) {
                    mediaStorageValue.AddItemListToMediaPool(filePathsArray).then(
                        function (project) {
                            debugLog(`Added clips: ${filePathsArray}`);
                        },
                        function (error) {
                            debugLog(`Error: Failed to add clips: ${filePathsArray}, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get media storage object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to get resolve object, ${error}`);
        }
    );
}

// Creates a new timeline with all the clips in current folder.
function createTimeline(event, timelineName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.GetCurrentProject().then(
                        function (currentProjectValue) {
                            currentProjectValue.GetMediaPool().then(
                                function (mediaPoolValue) {
                                    mediaPoolValue.GetCurrentFolder().then(
                                        function (currentFolderValue) {
                                            currentFolderValue.GetClipList().then(
                                                function (clipListValue) {
                                                    if (!clipListValue || (clipListValue.length === 0)) {
                                                        debugLog(`Error: Empty clip list`);
                                                        return null;
                                                    }

                                                    // Create timeline with clips
                                                    mediaPoolValue.CreateTimelineFromClips(timelineName, clipListValue).then(
                                                        function (newTimelineValue) {
                                                            debugLog(`Created timeline: ${timelineName}`);
                                                        },
                                                        function (error) {
                                                            debugLog(`Error: Failed to create timeline: ${timelineName}, ${error}`);
                                                        }
                                                    );
                                                },
                                                function (error) {
                                                    debugLog(`Error: Failed to get clip list, ${error}`);
                                                }
                                            );
                                        },
                                        function (error) {
                                            debugLog(`Error: Failed to get current folder object, ${error}`);
                                        }
                                    );
                                },
                                function (error) {
                                    debugLog(`Error: Failed to get media pool object, ${error}`);
                                }
                            );
                        },
                        function (error) {
                            debugLog(`Error: Failed to get curret project object, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Selects a timeline using name.
function selectTimeline(event, timelineName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.GetCurrentProject().then(
                        function (currentProjectValue) {
                            currentProjectValue.GetTimelineCount().then(
                                function (timelineCount) {
                                    if (!timelineCount || (timelineCount <= 0)) return;

                                    isDone = false;
                                    for (let i = 1; i <= timelineCount; i++) {
                                        if (isDone) return;
                                        currentProjectValue.GetTimelineByIndex(i).then(
                                            function (timelineValue) {
                                                if (isDone) return;
                                                timelineValue.GetName().then(
                                                    function (timelineNameValue) {
                                                        if (isDone) return;
                                                        if (timelineNameValue && (timelineNameValue === timelineName)) {
                                                            // Set current timeline
                                                            currentProjectValue.SetCurrentTimeline(timelineValue).then(
                                                                function (project) {
                                                                    debugLog(`Selected timeline: ${timelineName}`);
                                                                },
                                                                function (error) {
                                                                    debugLog(`Error: Failed to select timeline: ${timelineName}, ${error}`);
                                                                }
                                                            );

                                                            isDone = true;
                                                        }
                                                    },
                                                    function (error) {
                                                        // ignore
                                                    }
                                                );
                                            },
                                            function (error) {
                                                debugLog(`Error: Failed to get timeline object, ${error}`);
                                            }
                                        );
                                    }
                                },
                                function (error) {
                                    debugLog(`Error: Failed to get timeline count, ${error}`);
                                }
                            );
                        },
                        function (error) {
                            debugLog(`Error: Failed to get curret project object, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Render current timeline.
function renderTimeline(event, renderPresetName, targetDirPath, targetClipName) {
    getResolvePromise().then(
        function (resolveValue) {
            resolveValue.GetProjectManager().then(
                function (projectManagerValue) {
                    projectManagerValue.GetCurrentProject().then(
                        function (currentProjectValue) {
                            currentProjectValue.LoadRenderPreset(renderPresetName).then(
                                function (loadRenderPresetValue) {
                                    if (!loadRenderPresetValue) {
                                        debugLog(`Error: Failed to set render preset: ${loadRenderPresetValue}`);
                                        return;
                                    }

                                    currentProjectValue.SetRenderSettings({ "TargetDir": targetDirPath, "CustomName": targetClipName }).then(
                                        function (setRenderSettingsValue) {
                                            if (!setRenderSettingsValue) {
                                                debugLog("Error: Failed to set render settings");
                                                return;
                                            }

                                            currentProjectValue.AddRenderJob().then(
                                                function (jobId) {
                                                    if (!jobId) {
                                                        debugLog(`Failed to add render job`);
                                                        return;
                                                    }

                                                    debugLog(`Created render job with id: ${jobId}`);
                                                    currentProjectValue.StartRendering(jobId).then(
                                                        function (project) {
                                                            debugLog(`Started rendering job`);
                                                        },
                                                        function (error) {
                                                            debugLog(`Error: Failed to start rendering for job id: ${jobId}, ${error}`);
                                                        }
                                                    );
                                                },
                                                function (error) {
                                                    debugLog(`Error: Failed to add render job, ${error}`);
                                                }
                                            );
                                        },
                                        function (error) {
                                            debugLog(`Error: Failed to set render settings, ${error}`);
                                        }
                                    );
                                },
                                function (error) {
                                    debugLog(`Error: Failed to set render preset: ${renderPresetName}, ${error}`);
                                }
                            );
                        },
                        function (error) {
                            debugLog(`Error: Failed to get current project object, ${error}`);
                        }
                    );
                },
                function (error) {
                    debugLog(`Error: Failed to get project manager object, ${error}`);
                }
            );
        },
        function (error) {
            debugLog(`Error: Failed to resolve object, ${error}`);
        }
    );
}

// Gets render presets string list.
async function getRenderPresets() {
    resolve = await getResolvePromise();
    if (!resolve) return null;

    projectManager = await resolve.GetProjectManager();
    if (!projectManager) {
        console.log('Error: Failed to get ProjectManager object!');
        return null;
    }

    currentProject = await projectManager.GetCurrentProject();
    if (!currentProject) {
        console.log('Error: Failed to get current project object!');
    }

    return await currentProject.GetRenderPresetList();
}

// Register resolve event handler functions.
function registerResolveEventHandlers() {
    // Page
    ipcMain.handle('resolve:openPage', openPage);
    // Project
    ipcMain.handle('resolve:createProject', createProject);
    ipcMain.handle('resolve:saveProject', saveProject);
    ipcMain.handle('resolve:openProject', openProject);
    // Bin
    ipcMain.handle('resolve:createBin', createBin);
    ipcMain.handle('resolve:selectBin', selectBin);
    ipcMain.handle('resolve:deleteBin', deleteBin);
    // Clips
    ipcMain.handle('resolve:selectClipsToAdd', selectClipsToAdd);
    ipcMain.handle('resolve:addClips', addClips);
    // Timeline
    ipcMain.handle('resolve:createTimeline', createTimeline);
    ipcMain.handle('resolve:selectTimeline', selectTimeline);
    // Render
    ipcMain.handle('resolve:renderTimeline', renderTimeline);
    // RenderPreset
    ipcMain.handle('resolve:getRenderPresets', getRenderPresets);
    // Cleanup
    ipcMain.handle('resolve:cleanupResolveInterface', cleanupResolveInterface);
}

function createWindow () {
    // Create the browser window.
    mainWindow = new BrowserWindow({
        width: 900,
        height: 825,
        useContentSize: true,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js')
        }
    });

    // Hide the menu bar (enable below code to hide menu bar)
    //mainWindow.setMenu(null);

    mainWindow.on('close', function(e) {
        app.quit();
    });

    // Load index.html on the window.
    mainWindow.loadFile('index.html');

    // Open the DevTools (enable below code to show DevTools)
    //mainWindow.webContents.openDevTools();
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
    registerResolveEventHandlers();
    createWindow();
});

// Quit when all windows are closed.
app.on('window-all-closed', function () {
    // On macOS it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// In this file you can include the rest of your plugin specific main process
// code. You can also put them in separate files and require them here.
