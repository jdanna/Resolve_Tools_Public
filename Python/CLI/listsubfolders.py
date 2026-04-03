#!/usr/bin/env python3

import sys



# Adjust this path if needed for your OS
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
)

import DaVinciResolveScript as dvr

def main():
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("Unable to connect to DaVinci Resolve")
        return

    pm = resolve.GetProjectManager()
    projects = pm.GetFolderListInCurrentFolder()
    for folder in projects:
        print(f"{folder}")

if __name__ == "__main__":
    main()


