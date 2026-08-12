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


def GetBmd():
    try:
        # The PYTHONPATH needs to be set correctly for this import statement to work.
        # An alternative is to import the DaVinciResolveScript by specifying absolute path (see ExceptionHandler logic)
        import DaVinciResolveScript as bmd
        return bmd
    except ImportError:
        if sys.platform.startswith("darwin"):
            expectedPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            expectedPath = os.getenv('PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
        elif sys.platform.startswith("linux"):
            expectedPath = "/opt/resolve/Developer/Scripting/Modules/"

        # check if the default path has it...
        print("Unable to find module DaVinciResolveScript from $PYTHONPATH - trying default locations")
        try:
            load_source('DaVinciResolveScript', expectedPath + "DaVinciResolveScript.py")
            import DaVinciResolveScript as bmd
            return bmd
        except Exception as ex:
            # No fallbacks ... report error:
            print("Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
            print("For a default DaVinci Resolve installation, the module is expected to be located in: " + expectedPath)
            print(ex)
            sys.exit()


bmd = GetBmd()
resolve = bmd.scriptapp("Resolve")


# ---------------------------------------------------------------- mode dialog

fusion = resolve.Fusion()
ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

MODE_PROJECT = 'Project Settings'
MODE_MATCH = 'Match Clip'

result = {'mode': None}

win = dispatcher.AddWindow(
    {
        'ID': 'CreateTimelinesDialog',
        'WindowTitle': 'Create Timelines',
        'Geometry': [700, 300, 340, 110],
    },
    ui.VGroup({'Spacing': 8}, [
        ui.HGroup({'Spacing': 6}, [
            ui.Label({'Text': 'Timeline Settings:', 'Weight': 0}),
            ui.ComboBox({'ID': 'ModeCombo', 'Weight': 1}),
        ]),
        ui.HGroup({'Spacing': 6}, [
            ui.HGap(),
            ui.Button({'ID': 'CancelBtn', 'Text': 'Cancel', 'Weight': 0}),
            ui.Button({'ID': 'OKBtn', 'Text': 'OK', 'Weight': 0}),
        ]),
    ])
)

itm = win.GetItems()
itm['ModeCombo'].AddItem(MODE_PROJECT)
itm['ModeCombo'].AddItem(MODE_MATCH)


def OnOK(ev):
    result['mode'] = itm['ModeCombo'].CurrentText
    dispatcher.ExitLoop()


def OnCancel(ev):
    dispatcher.ExitLoop()


win.On['CreateTimelinesDialog'].Close = OnCancel
win.On['OKBtn'].Clicked = OnOK
win.On['CancelBtn'].Clicked = OnCancel

win.Show()
dispatcher.RunLoop()
win.Hide()

if not result['mode']:
    print("Cancelled.")
    sys.exit()

match_clip = result['mode'] == MODE_MATCH


# ------------------------------------------------------------------- helpers

def parse_resolution(clip):
    """Return (width, height) as strings, or None if the clip has no video."""
    res = clip.GetClipProperty('Resolution')
    if not res or 'x' not in str(res):
        return None
    width, _, height = str(res).partition('x')
    width = width.strip()
    height = height.strip()
    if not width.isdigit() or not height.isdigit():
        return None
    return width, height


def apply_clip_resolution(timeline, clip):
    """Match the timeline raster size to the clip. Frame rate is left alone."""
    resolution = parse_resolution(clip)
    if not resolution:
        return False

    # Without this the timeline just follows the project settings and every
    # SetSetting below is ignored.
    timeline.SetSetting('useCustomSettings', '1')

    width, height = resolution
    timeline.SetSetting('timelineResolutionWidth', width)
    timeline.SetSetting('timelineResolutionHeight', height)
    timeline.SetSetting('timelineOutputResolutionWidth', width)
    timeline.SetSetting('timelineOutputResolutionHeight', height)

    return True


# ---------------------------------------------------------------------- main

project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()

if not project:
    print("No project is open.")
    sys.exit()

media_pool = project.GetMediaPool()
current_bin = media_pool.GetCurrentFolder()
clips = current_bin.GetClipList()

if not clips:
    print("No clips found in the current bin.")
    sys.exit()

for clip in clips:
    if clip.GetClipProperty('Type') == "Timeline":
        continue

    clip_name = clip.GetName()
    timeline_name = os.path.splitext(clip_name)[0]  # Remove file extension
    start_tc = clip.GetClipProperty('Start TC')

    if match_clip:
        timeline = media_pool.CreateEmptyTimeline(timeline_name)
        if not timeline:
            print("Failed to create timeline for " + clip_name)
            continue

        # Applied to the empty timeline, before anything is appended.
        if not apply_clip_resolution(timeline, clip):
            print("No resolution on " + clip_name + " - using project settings.")

        project.SetCurrentTimeline(timeline)
        if not media_pool.AppendToTimeline([clip]):
            print("Failed to append " + clip_name + " to its timeline.")
    else:
        timeline = media_pool.CreateTimelineFromClips(timeline_name, clip)

    # Fails when the clip's timecode isn't valid at the timeline's frame rate -
    # e.g. frame 24 of a 29.97 clip on a 23.976 timeline. Resolve returns False
    # rather than raising, so it goes unnoticed unless it's checked.
    if timeline and start_tc:
        if not timeline.SetStartTimecode(start_tc):
            print("Could not set start timecode " + str(start_tc) + " on " + timeline_name
                  + " - not a valid timecode at the timeline's frame rate.")
