// This file is required by the index.html file and will
// be executed in the renderer process for that window.

let selectedClipsToAdd = [];

// Perform action on DOM loaded.
window.addEventListener('DOMContentLoaded', async () => {
});

// Perform action on DOM unloaded.
window.addEventListener('beforeunload', async function (e) {
    await window.resolveAPI.cleanupResolveInterface();
});

// Creates a new project.
function createProject() {
    const projName = document.getElementById('projName').value;
    if (!projName) {
        alert('Error: Project name is empty!');
        return;
    }

    window.resolveAPI.createProject(projName);
}

// Opens a project.
function openProject() {
    const projName = document.getElementById('projName').value;
    if (!projName) {
        alert('Error: Project name is empty!');
        return;
    }

    window.resolveAPI.openProject(projName);
}

// Saves current project.
function saveProject() {
    window.resolveAPI.saveProject();
}

// Creates a new bin.
function createBin() {
    const binName = document.getElementById('binName').value;
    if (!binName) {
        alert('Error: Bin name is empty!');
        return;
    }

    // Create new bin in root bin
    window.resolveAPI.createBin(binName)
}

// Selects a bin.
function selectBin() {
    const binName = document.getElementById('binName').value;
    if (!binName) {
        alert('Error: Bin name is empty!');
        return;
    }

    window.resolveAPI.selectBin(binName)
}

// Deletes a bin.
function deleteBin() {
    const binName = document.getElementById('binName').value;
    if (!binName) {
        alert('Error: Bin name is empty!');
        return;
    }

    window.resolveAPI.deleteBin(binName)
}

// Select clips to add.
async function selectClipsToAdd() {
    document.getElementById("selectedFilesText").value = "";
    selectedClipsToAdd = await window.resolveAPI.selectClipsToAdd();
    if (selectedClipsToAdd) {
        document.getElementById("selectedFilesText").value = selectedClipsToAdd;
        console.log(`Selected files: ${selectedClipsToAdd}`);
    }
}

// Add clips to media pool.
function addClips() {
    if (!selectedClipsToAdd || (selectedClipsToAdd.length === 0)) {
        alert('Error: Empty file list, select some clips and try again');
        return;
    }

    // Add clips to the current folder
    window.resolveAPI.addClips(selectedClipsToAdd)
}

// Creates a new timeline with all the clips in current folder.
function createTimeline() {
    const timelineName = document.getElementById('timelineName').value;
    if (!timelineName) {
        alert('Error: Timeline name is empty!');
        return;
    }

    // Create timeline with current folder clips
    window.resolveAPI.createTimeline(timelineName);
}

// Selects a timeline using name.
function selectTimeline() {
    const timelineName = document.getElementById('timelineName').value;
    if (!timelineName) {
        alert('Error: Timeline name is empty!');
        return;
    }

    // Set current timeline
    window.resolveAPI.selectTimeline(timelineName);
}

// Load render presets.
async function loadRenderPresets() {
    var cbRenderPreset = document.getElementById('cbRenderPreset');

    if (!cbRenderPreset.options || (cbRenderPreset.options.length === 0)) {
        const renderPresetList = await window.resolveAPI.getRenderPresets();
        if (!renderPresetList) {
            console.log(`Error: Empty render preset list`);
            return;
        }

        for (var index in renderPresetList) {
            option = document.createElement('option');
            option.text = renderPresetList[index];
            option.value = renderPresetList[index];
            cbRenderPreset.appendChild(option);
        }

        console.log(`Loaded render presets`);
    }
}

// Render current timeline.
async function renderTimeline() {
    const targetDirPath = document.getElementById('targetDirPath').value;
    if (!targetDirPath) {
        alert('Error: Target directory path is empty!');
        return;
    }

    const targetClipName = document.getElementById('targetClipName').value;
    if (!targetClipName) {
        alert('Error: Target clip name is empty!');
        return;
    }

    const renderPresetName = document.getElementById('cbRenderPreset').value;
    if (!renderPresetName) {
        alert('Error: Render preset name is empty, load render presets and try again');
        return;
    }

    await window.resolveAPI.openPage('deliver');

    // Start rendering render job
    window.resolveAPI.renderTimeline(renderPresetName, targetDirPath, targetClipName);
}
