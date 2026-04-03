#!/usr/bin/env python3
import json
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
    folders = pm.GetFolderListInCurrentFolder() or []
    
# Output as JSON array
 
    print(json.dumps(list(folders), indent=2))
if __name__ == "__main__":
    main()


