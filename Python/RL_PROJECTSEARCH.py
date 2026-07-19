"""RL_PROJECTSEARCH

Standalone search tool for the DaVinci Resolve Project Manager database.

Indexes every project across every folder in the current database (recursively,
starting from root) and shows them in a searchable list. Type in the search box to
filter by project name (case insensitive), select a result, then:

- Open        - loads the selected project.
- Open Folder - navigates the Project Manager to the project's folder and closes
                the current project so Resolve shows the Project Manager there.
                (The scripting API has no call to pop open the Project Manager
                panel directly - closing the active project is the only way to
                make Resolve display it.)
- Export      - asks for a destination folder and exports the project as a .drp.
                If a file of that name already exists, offers to overwrite it or
                save alongside it as "<name>-1.drp", "-2.drp", etc.
- Refresh     - re-indexes the database (in case projects changed since launch).
- Close       - closes this script.

Open / Open Folder / Export never close the script, so you can act on several
projects in one session.

Unlike the scripts in Python/CLI/, this is meant to be run as a plain standalone
Python process (double-clicked or run from a terminal) rather than from Resolve's
Workspace > Scripts menu, so it does its own DaVinciResolveScript module bootstrap.
DaVinci Resolve must already be running.
"""

import sys
import os
import traceback


# ---------------------------------------------------------------------------
# Resolve bootstrap (standard repo pattern - see RL_XML_NOTCH.py)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Project Manager indexing
# ---------------------------------------------------------------------------

def walk(pm, path_names, results, on_progress=None):
    """Recursively collect {'name', 'path'} entries for every project under the
    current folder. 'path' is the list of folder names from root down to (but
    not including) the project itself. Leaves the current folder unchanged."""
    for name in (pm.GetProjectListInCurrentFolder() or []):
        results.append({'name': name, 'path': list(path_names)})

    if on_progress:
        on_progress(len(results), format_path(path_names))

    for folder in (pm.GetFolderListInCurrentFolder() or []):
        if pm.OpenFolder(folder):
            walk(pm, path_names + [folder], results, on_progress)
            pm.GotoParentFolder()


def build_index(pm, on_progress=None):
    pm.GotoRootFolder()
    results = []
    walk(pm, [], results, on_progress)
    return results


def goto(pm, path):
    """Navigate the Project Manager's current folder to the given path (list of
    folder names from root)."""
    pm.GotoRootFolder()
    for folder in path:
        pm.OpenFolder(folder)


def format_path(path):
    return '/' + '/'.join(path) if path else '/'


def unique_export_path(file_path):
    """Return file_path unchanged if free, else '<name>-1.drp', '-2.drp', etc."""
    base, ext = os.path.splitext(file_path)
    candidate = file_path
    n = 1
    while os.path.exists(candidate):
        candidate = "%s-%d%s" % (base, n, ext)
        n += 1
    return candidate


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def prompt_overwrite(ui, dispatcher, file_path):
    """Modal Overwrite / Save as New / Cancel prompt. Returns one of those
    three strings. Mirrors the AddWindow + Show/RunLoop/Hide pattern used
    throughout this repo (see RL_XML_NOTCH.py's show_message)."""
    result = {'choice': 'cancel'}

    win = dispatcher.AddWindow(
        {'ID': 'OverwriteDialog', 'WindowTitle': 'File Exists', 'Geometry': [700, 300, 480, 130]},
        ui.VGroup({'Spacing': 8}, [
            ui.Label({'Text': "%s\nalready exists." % file_path, 'WordWrap': True}),
            ui.HGroup({'Spacing': 6, 'Weight': 0}, [
                ui.HGap(),
                ui.Button({'ID': 'CancelBtn', 'Text': 'Cancel', 'Weight': 0}),
                ui.Button({'ID': 'SaveAsNewBtn', 'Text': 'Save as New', 'Weight': 0}),
                ui.Button({'ID': 'OverwriteBtn', 'Text': 'Overwrite', 'Weight': 0}),
            ]),
        ])
    )

    def choose(choice):
        def handler(ev):
            result['choice'] = choice
            dispatcher.ExitLoop()
        return handler

    win.On['OverwriteDialog'].Close = choose('cancel')
    win.On['CancelBtn'].Clicked = choose('cancel')
    win.On['SaveAsNewBtn'].Clicked = choose('increment')
    win.On['OverwriteBtn'].Clicked = choose('overwrite')

    win.Show()
    dispatcher.RunLoop()
    win.Hide()

    return result['choice']


def run_search_window(fusion, ui, dispatcher, pm):
    all_entries = []
    state = {'filtered': []}

    win = dispatcher.AddWindow(
        {'ID': 'ProjectSearchWindow', 'WindowTitle': 'RL Project Search', 'Geometry': [400, 200, 640, 480]},
        ui.VGroup({'Spacing': 8}, [
            ui.LineEdit({'ID': 'SearchBox', 'PlaceholderText': 'Search projects...', 'Weight': 0}),
            ui.Tree({'ID': 'ResultsTree', 'ColumnCount': 2, 'Weight': 1, 'SortingEnabled': True}),
            ui.Label({'ID': 'StatusLabel', 'Text': '', 'Weight': 0}),
            ui.VGap(12),
            ui.HGroup({'Spacing': 6, 'Weight': 0}, [
                ui.HGap(),
                ui.Button({'ID': 'OpenBtn', 'Text': 'Open', 'Weight': 0}),
                ui.Button({'ID': 'OpenFolderBtn', 'Text': 'Open Folder', 'Weight': 0}),
                ui.Button({'ID': 'ExportBtn', 'Text': 'Export', 'Weight': 0}),
                ui.HGap(16),
                ui.Button({'ID': 'RefreshBtn', 'Text': 'Refresh', 'Weight': 0}),
                ui.Button({'ID': 'CloseBtn', 'Text': 'Close', 'Weight': 0}),
            ]),
            ui.VGap(12),
        ])
    )

    itm = win.GetItems()
    tree = itm['ResultsTree']
    tree.SetHeaderLabels(['Project', 'Folder'])
    tree.ColumnWidth[0] = 340

    def set_status(text):
        itm['StatusLabel'].Text = text

    def refresh_list(query):
        q = query.strip().lower()
        matched = [e for e in all_entries if not q or q in e['name'].lower()]
        if matched == state['filtered']:
            return
        state['filtered'] = matched
        tree.Clear()
        for entry in matched:
            item = tree.NewItem()
            item.Text[0] = entry['name']
            item.Text[1] = format_path(entry['path'])
            tree.AddTopLevelItem(item)
        set_status("%d project(s)" % len(matched))

    def report_progress(count, folder_display):
        set_status("Indexing... %d project(s) found (in %s)" % (count, folder_display))
        itm['StatusLabel'].Repaint()

    def reindex():
        nonlocal all_entries
        set_status("Indexing project database...")
        itm['StatusLabel'].Repaint()
        entries = build_index(pm, report_progress)
        entries.sort(key=lambda e: e['name'].lower())
        all_entries = entries
        state['filtered'] = None  # force refresh_list to rebuild even if unchanged
        refresh_list(itm['SearchBox'].Text)

    def get_selected_entry():
        # SelectedItems() returns a dict of {row_index: item}, not a list -
        # use .values(). Row index/Python object identity are both unreliable
        # once SortingEnabled reorders rows or the item is re-fetched, so the
        # match back to our data is by the item's own displayed text instead.
        selected = tree.SelectedItems()
        if not selected:
            return None
        item = list(selected.values())[0]
        name, folder = item.Text[0], item.Text[1]
        for entry in state['filtered']:
            if entry['name'] == name and format_path(entry['path']) == folder:
                return entry
        return None

    def OnSearchChanged(ev):
        refresh_list(itm['SearchBox'].Text)

    def OnOpen(ev):
        entry = get_selected_entry()
        if not entry:
            set_status("Select a project first.")
            print("Open: no project selected.")
            return
        print("Opening %r in %s ..." % (entry['name'], format_path(entry['path'])))
        goto(pm, entry['path'])
        project = pm.LoadProject(entry['name'])
        if not project:
            set_status("Could not open project %r." % entry['name'])
            print("LoadProject(%r) failed." % entry['name'])
            return
        set_status("Opened %r." % entry['name'])

    def OnOpenFolder(ev):
        entry = get_selected_entry()
        if not entry:
            set_status("Select a project first.")
            print("Open Folder: no project selected.")
            return
        print("Opening folder %s ..." % format_path(entry['path']))
        goto(pm, entry['path'])
        current = pm.GetCurrentProject()
        if current:
            pm.CloseProject(current)
        set_status("Opened folder %s in the Project Manager." % format_path(entry['path']))

    def OnExport(ev):
        entry = get_selected_entry()
        if not entry:
            set_status("Select a project first.")
            print("Export: no project selected.")
            return
        try:
            folder = fusion.RequestDir()
        except Exception as ex:
            set_status("Folder browser unavailable (%s)." % ex)
            print("fusion.RequestDir() failed: %s" % ex)
            return
        if not folder:
            print("Export cancelled.")
            return
        file_path = os.path.join(str(folder), entry['name'] + ".drp")
        if os.path.exists(file_path):
            choice = prompt_overwrite(ui, dispatcher, file_path)
            if choice == 'cancel':
                set_status("Export cancelled.")
                return
            if choice == 'increment':
                file_path = unique_export_path(file_path)
        goto(pm, entry['path'])
        print("Exporting %r to %s ..." % (entry['name'], file_path))
        if pm.ExportProject(entry['name'], file_path):
            set_status("Exported to %s" % file_path)
        else:
            set_status("Export failed for %r." % entry['name'])
            print("ExportProject(%r, %r) returned False." % (entry['name'], file_path))

    def OnRefresh(ev):
        reindex()

    def OnClose(ev):
        dispatcher.ExitLoop()

    def bind(widget_id, event_name, handler):
        # A single unsupported event name must not stop the rest of the
        # bindings below it from registering, so each is isolated. The handler
        # itself is also wrapped so an exception inside it is printed with a
        # full traceback instead of silently vanishing.
        def safe_handler(ev):
            try:
                handler(ev)
            except Exception:
                print("ERROR handling %s.%s:" % (widget_id, event_name))
                traceback.print_exc()
        try:
            setattr(win.On[widget_id], event_name, safe_handler)
        except Exception as ex:
            print("Could not bind %s.%s: %s" % (widget_id, event_name, ex))

    bind('ProjectSearchWindow', 'Close', OnClose)
    bind('OpenBtn', 'Clicked', OnOpen)
    bind('OpenFolderBtn', 'Clicked', OnOpenFolder)
    bind('ExportBtn', 'Clicked', OnExport)
    bind('RefreshBtn', 'Clicked', OnRefresh)
    bind('CloseBtn', 'Clicked', OnClose)
    bind('SearchBox', 'TextChanged', OnSearchChanged)

    # Show the window first so the user sees indexing progress rather than a
    # blank/frozen UI while the (potentially slow) recursive folder walk runs.
    win.Show()
    try:
        reindex()
    except Exception:
        # If indexing itself fails, still fall through to RunLoop() below -
        # otherwise no button would ever respond, since the event loop would
        # never even start. Better an empty list you can Refresh/Close than a
        # dead window.
        print("ERROR during initial indexing:")
        traceback.print_exc()
        set_status("Indexing failed - see console. Try Refresh.")
    dispatcher.RunLoop()
    win.Hide()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    bmd = GetBmd()
    resolve = bmd.scriptapp("Resolve")
    if not resolve:
        print("Unable to connect to DaVinci Resolve. Make sure Resolve is running.")
        sys.exit(1)

    fusion = resolve.Fusion()
    ui = fusion.UIManager
    dispatcher = bmd.UIDispatcher(ui)

    pm = resolve.GetProjectManager()
    if not pm:
        print("ERROR: Could not get ProjectManager")
        sys.exit(1)

    try:
        run_search_window(fusion, ui, dispatcher, pm)
    except Exception:
        print("FATAL ERROR setting up the window:")
        traceback.print_exc()
        raise
    print("Done.")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
