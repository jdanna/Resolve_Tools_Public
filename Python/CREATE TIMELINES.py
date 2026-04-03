import sys
import os


def load_source(module_name, file_path):
    if sys.version_info[0] >= 3 and sys.version_info[1] >= 5:
        import importlib.util
        module = None
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec:
            module = importlib.util.module_from_spec(spec)
        if module:
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        return module
    else:
        import imp
        return imp.load_source(module_name, file_path)


def GetResolve():
    try:
        # The PYTHONPATH needs to be set correctly for this import statement to work.
        # An alternative is to import the DaVinciResolveScript by specifying absolute path (see ExceptionHandler logic)
        import DaVinciResolveScript as bmd
    except ImportError:
        if sys.platform.startswith("darwin"):
            expectedPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            import os
            expectedPath = os.getenv('PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
        elif sys.platform.startswith("linux"):
            expectedPath = "/opt/resolve/Developer/Scripting/Modules/"

        # check if the default path has it...
        print("Unable to find module DaVinciResolveScript from $PYTHONPATH - trying default locations")
        try:
            load_source('DaVinciResolveScript', expectedPath + "DaVinciResolveScript.py")
            import DaVinciResolveScript as bmd
        except Exception as ex:
            # No fallbacks ... report error:
            print("Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
            print("For a default DaVinci Resolve installation, the module is expected to be located in: " + expectedPath)
            print(ex)
            sys.exit()

    return bmd.scriptapp("Resolve")



resolve = GetResolve()

project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()

if not project:
    print("No project is open.")


media_pool = project.GetMediaPool()
current_bin = media_pool.GetCurrentFolder()
clips = current_bin.GetClipList()

if not clips:
    print("No clips found in the current bin.")

for clip in clips:
    if clip.GetClipProperty('Type') == "Timeline":
        continue

    clip_name = clip.GetName()
    timeline_name = os.path.splitext(clip_name)[0]  # Remove file extension
    start_tc = clip.GetClipProperty('Start TC')

    timeline = media_pool.CreateTimelineFromClips(timeline_name, clip)
    if timeline and start_tc:
        timeline.SetStartTimecode(start_tc)
