import sys
import os
lib_path = os.getenv("RESOLVE_SCRIPT_LIB")


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
        import DaVinciResolveScript as bmd
        return bmd
    except ImportError:
        if sys.platform.startswith("darwin"):
            expectedPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            expectedPath = os.getenv('PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
        elif sys.platform.startswith("linux"):
            expectedPath = "/opt/resolve/Developer/Scripting/Modules/"

        print("Unable to find module DaVinciResolveScript from $PYTHONPATH - trying default locations")
        try:
            load_source('DaVinciResolveScript', expectedPath + "DaVinciResolveScript.py")
            import DaVinciResolveScript as bmd
            return bmd
        except Exception as ex:
            print("Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
            print("For a default DaVinci Resolve installation, the module is expected to be located in: " + expectedPath)
            print(ex)
            sys.exit()


bmd = GetBmd()
resolve = bmd.scriptapp("Resolve")

fusion = resolve.Fusion()
ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

result = {'tc': None, 'confirmed': False}

win = dispatcher.AddWindow(
    {
        'ID': 'SetSeqTCDialog',
        'WindowTitle': 'Batch Set Sequence Timecode',
        'Geometry': [700, 300, 320, 100],
    },
    ui.VGroup({'Spacing': 8}, [
        ui.HGroup({'Spacing': 6}, [
            ui.Label({'Text': 'New Timecode:', 'Weight': 0}),
            ui.LineEdit({'ID': 'TCInput', 'PlaceholderText': '00:00:00:00', 'Weight': 1}),
        ]),
        ui.HGroup({'Spacing': 6}, [
            ui.HGap(),
            ui.Button({'ID': 'CancelBtn', 'Text': 'Cancel', 'Weight': 0}),
            ui.Button({'ID': 'OKBtn', 'Text': 'OK', 'Weight': 0}),
        ]),
    ])
)

itm = win.GetItems()

def OnOK(ev):
    result['tc'] = itm['TCInput'].Text
    result['confirmed'] = True
    dispatcher.ExitLoop()

def OnCancel(ev):
    dispatcher.ExitLoop()

def OnClose(ev):
    dispatcher.ExitLoop()

win.On['SetSeqTCDialog'].Close = OnClose
win.On['OKBtn'].Clicked = OnOK
win.On['CancelBtn'].Clicked = OnCancel

win.Show()
dispatcher.RunLoop()
win.Hide()

if not result['confirmed'] or not result['tc']:
    print("Cancelled.")
    sys.exit()

tc = result['tc']

projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()
mediapool = project.GetMediaPool()
folder = mediapool.GetCurrentFolder()
cliplist = folder.GetClipList()
numtimelines = project.GetTimelineCount()

for i in cliplist:
    if i.GetClipProperty('Type') == "Timeline":
        name = i.GetClipProperty('Clip Name')
        for t in range(1, numtimelines + 1):
            timeline = project.GetTimelineByIndex(t)
            if timeline.GetName() == name:
                timeline.SetStartTimecode(tc)
                print("SET TC " + tc + " ON SEQUENCE: " + name)
