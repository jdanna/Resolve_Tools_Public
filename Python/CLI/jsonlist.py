#!/usr/bin/env python3

import json
import sys

sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
)

try:
    import DaVinciResolveScript as dvr
except ImportError:
    print("ERROR: DaVinciResolveScript module not found")
    sys.exit(1)

resolve = dvr.scriptapp("Resolve")
pm = resolve.GetProjectManager()

if not pm:
    print("ERROR: Could not get ProjectManager")
    sys.exit(1)

def walk_project_folders(pm):
    """
    Recursively walk Project Manager folders WITHOUT opening projects
    """

    data = {
        "folder_name": pm.GetCurrentFolder(),
        "projects": [],
        "subfolders": []
    }

    # Get projects in this folder
    projects = pm.GetProjectListInCurrentFolder() or []
    data["projects"] = list(projects)

    # Get subfolders
    folders = pm.GetFolderListInCurrentFolder() or []

    for folder in folders:
        pm.OpenFolder(folder)
        data["subfolders"].append(walk_project_folders(pm))
        pm.GotoParentFolder()

    return data

# Start from root
pm.GotoRootFolder()

project_tree = walk_project_folders(pm)

print(json.dumps(project_tree, indent=2))
