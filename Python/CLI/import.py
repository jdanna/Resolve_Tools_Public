#!/usr/bin/env python3
import shutil
import os
import sys
name = sys.argv[1]


# Adjust this path if needed for your OS
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
)

import DaVinciResolveScript as dvr

def main():
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("Unable to connect to DaVinci Resolve")
        return
    template = "/home/jdanna/jd.drp"
    newpath = "/tmp/"+name+".drp"
    shutil.copy2(template,newpath)
    pm = resolve.GetProjectManager()
    pm.ImportProject(newpath)
    os.remove(newpath)

if __name__ == "__main__":
    main()


