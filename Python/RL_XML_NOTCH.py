"""RL_XML_NOTCH

Notch a baked (flattened) render of a Premiere Pro timeline back into its
original edit structure inside DaVinci Resolve.

Select the baked clip in the media pool, run the script, and point it at the
FCP7/xmeml XML export of the Premiere timeline. The script builds a new
timeline containing the baked clip cut at every edit point from the XML, with
cross dissolves recreated where the XML had transitions (including fades
to/from black) and empty gaps wherever no video track had a clip. The timeline
start timecode matches the clip's start timecode, so timeline position equals
source timecode frame-for-frame.

Options:
- Treat all transitions as cuts: no dissolves are created; transitions
  between clips become a single cut at the center of the transition span,
  and fades to/from black leave a solid clip covering the full span.
- Treat edge transitions as cuts: dissolves between clips are kept, but a
  fade to/from black at either edge of a clip becomes a plain cut.

The Resolve API cannot add razor cuts or transitions, so the timeline is
described as an OpenTimelineIO (.otio) file - generated directly as JSON with
the standard library, no opentimelineio package needed - and imported with
MediaPool.ImportTimelineFromFile(), relinking to the selected pool clip.

Requires Resolve 18.5+ (MediaPool.GetSelectedClips).
"""

import sys
import os
import re
import json
import tempfile
import xml.etree.ElementTree as ET


# ---------------------------------------------------------------------------
# Timecode / rate helpers
# ---------------------------------------------------------------------------

def frames_to_timecode(total_frames, fps, drop_frame=False):
    """Convert a frame count to a timecode string.

    Drop frame is only valid for 29.97 (nominal 30) and 59.94 (nominal 60).
    Drop frame timecodes use ';' as the frames separator per SMPTE convention.
    """
    fps_round = int(round(fps))

    if drop_frame and fps_round in (30, 60):
        # SMPTE drop frame: skip frame numbers 00 and 01 (or 00–03 for 59.94)
        # at the start of every minute, except every 10th minute.
        drop = 2 if fps_round == 30 else 4

        frames_per_minute = fps_round * 60 - drop        # frames in non-10th minutes
        frames_per_10_min = frames_per_minute * 10 + drop # frames in a 10-minute block
        frames_per_hour   = frames_per_10_min * 6

        total_frames = total_frames % (frames_per_hour * 24)

        hours     = total_frames // frames_per_hour
        remaining = total_frames  % frames_per_hour

        ten_min_blocks = remaining // frames_per_10_min
        remaining      = remaining  % frames_per_10_min

        # The first minute of each 10-minute block has a full fps_round*60 frames;
        # every subsequent minute is shorter by 'drop'.
        first_min_frames = fps_round * 60
        if remaining < first_min_frames:
            minute_in_block = 0
            frames_in_min   = remaining
        else:
            remaining       -= first_min_frames
            minute_in_block  = remaining // frames_per_minute + 1
            frames_in_min    = remaining  % frames_per_minute + drop

        total_minutes = ten_min_blocks * 10 + minute_in_block
        secs   = frames_in_min // fps_round
        frames = frames_in_min  % fps_round

        return f"{hours:02}:{total_minutes:02}:{secs:02};{frames:02}"

    else:
        # Non-drop frame (works for all integer and fractional non-DF rates)
        hours   = total_frames // (3600 * fps_round)
        minutes = (total_frames % (3600 * fps_round)) // (60 * fps_round)
        secs    = (total_frames % (60  * fps_round)) // fps_round
        frames  = total_frames  % fps_round

        return f"{hours:02}:{minutes:02}:{secs:02}:{frames:02}"


def tc_to_frames(tc_str, fps):
    """Convert a timecode string to a frame count.

    Drop frame is detected from a ';' or ',' frames separator and is only
    valid for 29.97 (nominal 30) and 59.94 (nominal 60).
    """
    fps_round = int(round(fps))
    drop_frame = ';' in tc_str or ',' in tc_str

    parts = tc_str.replace(';', ':').replace(',', ':').split(':')
    if len(parts) != 4:
        raise ValueError("Bad timecode: %r" % tc_str)
    hh, mm, ss, ff = (int(x) for x in parts)

    frames = ((hh * 3600 + mm * 60 + ss) * fps_round) + ff

    if drop_frame and fps_round in (30, 60):
        drop = 2 if fps_round == 30 else 4
        total_minutes = hh * 60 + mm
        frames -= drop * (total_minutes - total_minutes // 10)

    return frames


def exact_rate(fps):
    """Map a rounded NTSC-family rate to its exact rational value.

    Resolve reports 23.976 etc. via GetClipProperty; its own OTIO files use
    the exact 24000/1001 form, so we match that.
    """
    ntsc = {24: 24000.0 / 1001.0, 30: 30000.0 / 1001.0,
            48: 48000.0 / 1001.0, 60: 60000.0 / 1001.0,
            120: 120000.0 / 1001.0}
    fps = float(fps)
    fps_round = int(round(fps))
    if fps_round in ntsc and abs(fps - ntsc[fps_round]) < 0.05 and fps != fps_round:
        return ntsc[fps_round]
    return fps


# ---------------------------------------------------------------------------
# FCP7 / xmeml parsing
# ---------------------------------------------------------------------------

ALIGN_CENTER = ('center',)
ALIGN_START = ('start', 'start-black')
ALIGN_END = ('end', 'end-black')


def parse_rate(rate_elem):
    """Return (fps, timebase) from an xmeml <rate> element."""
    timebase = int(rate_elem.findtext('timebase', '0'))
    ntsc = rate_elem.findtext('ntsc', 'FALSE').strip().upper() == 'TRUE'
    fps = timebase * 1000.0 / 1001.0 if ntsc else float(timebase)
    return fps, timebase


def parse_xmeml(xml_path, warn=print):
    """Parse an FCP7/xmeml file.

    Returns {'name', 'fps', 'timebase', 'duration', 'tracks'} for the first
    sequence, where tracks is the list of enabled video <track> elements.
    """
    root = ET.parse(xml_path).getroot()
    sequences = root.findall('.//sequence')
    if not sequences:
        raise ValueError("No <sequence> found in XML")
    if len(sequences) > 1:
        warn("WARNING: XML contains %d sequences - using the first (%r)"
             % (len(sequences), sequences[0].findtext('name', '?')))
    seq = sequences[0]

    rate_elem = seq.find('rate')
    if rate_elem is None:
        raise ValueError("Sequence has no <rate>")
    fps, timebase = parse_rate(rate_elem)

    duration = int(seq.findtext('duration', '0'))

    tracks = []
    for track in seq.findall('./media/video/track'):
        if track.findtext('enabled', 'TRUE').strip().upper() == 'FALSE':
            continue
        tracks.append(track)
    if not tracks:
        raise ValueError("Sequence has no enabled video tracks")

    return {
        'name': seq.findtext('name', 'sequence'),
        'fps': fps,
        'timebase': timebase,
        'duration': duration,
        'tracks': tracks,
    }


def _transition_info(el, warn=print):
    """Return (start, end, cut, in_off, out_off) for a <transitionitem>."""
    t_start = int(el.findtext('start', '-1'))
    t_end = int(el.findtext('end', '-1'))
    alignment = el.findtext('alignment', 'center').strip().lower()
    if alignment in ALIGN_START:
        cut = t_start
    elif alignment in ALIGN_END:
        cut = t_end
    else:
        if alignment not in ALIGN_CENTER:
            warn("WARNING: unknown transition alignment %r at frame %d - treating as center"
                 % (alignment, t_start))
        cut = (t_start + t_end) // 2
    return t_start, t_end, cut, cut - t_start, t_end - cut


def _edge_governed(clip_el, which, t_start, t_end):
    """True if the clip's 'start'/'end' edge is governed by a transition
    spanning [t_start, t_end] (edge is -1 or falls within the span)."""
    v = int(clip_el.findtext(which, '-1'))
    return v < 0 or t_start <= v <= t_end


def resolve_track(track_elem, all_as_cuts=False, edge_as_cuts=False, warn=print):
    """Resolve one video track's items into concrete extents and cut points.

    Returns (intervals, cuts, transitions):
      intervals   - list of (start, end) actual occupied extents
      cuts        - set of notional edit-point frames
      transitions - dict cut_frame -> (in_offset, out_offset)
    Handles clipitem start/end == -1 (edge governed by the adjacent
    transitionitem) and transition-adjacent concrete edges.

    all_as_cuts  - emit no dissolves at all: transitions between clips become
                   a cut at the center of the transition span; edge fades
                   (to/from black) leave a solid clip covering the full span.
    edge_as_cuts - keep dissolves between clips, but edge fades become plain
                   clip/black boundaries (solid clip covering the full span).
    """
    items = []
    for child in track_elem:
        if child.tag == 'clipitem':
            if child.findtext('enabled', 'TRUE').strip().upper() == 'FALSE':
                continue
            items.append(('clip', child))
        elif child.tag == 'transitionitem':
            items.append(('trans', child))

    intervals = []
    cuts = set()
    transitions = {}

    for i, (kind, el) in enumerate(items):
        if kind == 'trans':
            t_start, t_end, cut, in_off, out_off = _transition_info(el, warn)
            prev = items[i - 1] if i > 0 else None
            nxt = items[i + 1] if i < len(items) - 1 else None
            between_clips = (
                prev and prev[0] == 'clip' and _edge_governed(prev[1], 'end', t_start, t_end)
                and nxt and nxt[0] == 'clip' and _edge_governed(nxt[1], 'start', t_start, t_end))
            if all_as_cuts:
                # No dissolve. Between clips: cut at the transition center.
                # Edge fade: the clip already extends over the full span, so
                # its interval boundary is the only edit needed.
                if between_clips:
                    cuts.add((t_start + t_end) // 2)
            elif edge_as_cuts and not between_clips:
                pass  # fade to/from black -> plain boundary at the span edge
            else:
                transitions[cut] = (in_off, out_off)
                cuts.add(cut)
            continue

        start = int(el.findtext('start', '-1'))
        end = int(el.findtext('end', '-1'))
        name = el.findtext('name', '?')
        prev = items[i - 1] if i > 0 else None
        nxt = items[i + 1] if i < len(items) - 1 else None

        # An edge is governed by a neighboring transitionitem only when the
        # transition temporally contains that edge (or the edge is -1): the
        # clip then extends under the whole transition span, and the notional
        # cut is the transition's alignment point (already recorded above).
        # A document-adjacent transition that doesn't touch the edge belongs
        # to the other side of a gap on this track.
        governed = False
        if prev and prev[0] == 'trans':
            t_start = int(prev[1].findtext('start', '-1'))
            t_end = int(prev[1].findtext('end', '-1'))
            if start < 0 or t_start <= start <= t_end:
                start = t_start
                governed = True
        if not governed:
            if start < 0:
                warn("WARNING: clipitem %r has start=-1 with no adjacent transition - skipped" % name)
                continue
            cuts.add(start)

        governed = False
        if nxt and nxt[0] == 'trans':
            t_start = int(nxt[1].findtext('start', '-1'))
            t_end = int(nxt[1].findtext('end', '-1'))
            if end < 0 or t_start <= end <= t_end:
                end = t_end
                governed = True
        if not governed:
            if end < 0:
                warn("WARNING: clipitem %r has end=-1 with no adjacent transition - skipped" % name)
                continue
            cuts.add(end)

        if end > start:
            intervals.append((start, end))

    return intervals, cuts, transitions


def merge_intervals(intervals):
    """Merge overlapping or touching (start, end) intervals."""
    merged = []
    for s, e in sorted(intervals):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def build_cutlist(tracks, seq_duration, all_as_cuts=False, edge_as_cuts=False, warn=print):
    """Flatten all video tracks into one segment list plus transitions.

    Returns (segments, transitions):
      segments    - ordered list of ('clip'|'gap', start, end) covering
                    [0, duration); 'gap' = black (no clip on any track)
      transitions - dict boundary_frame -> (in_offset, out_offset)
    See resolve_track for the all_as_cuts / edge_as_cuts options.
    """
    all_intervals = []
    all_cuts = set()
    all_transitions = {}

    for track in tracks:
        intervals, cuts, transitions = resolve_track(track, all_as_cuts, edge_as_cuts, warn)
        all_intervals += intervals
        all_cuts |= cuts
        for cut, (in_off, out_off) in transitions.items():
            if cut in all_transitions and all_transitions[cut] != (in_off, out_off):
                old = all_transitions[cut]
                if in_off + out_off <= old[0] + old[1]:
                    continue
                warn("WARNING: overlapping transitions at frame %d on multiple tracks - keeping the longer" % cut)
            all_transitions[cut] = (in_off, out_off)

    occupied = merge_intervals(all_intervals)
    if not occupied:
        raise ValueError("No clips found on any video track")

    duration = max(seq_duration, occupied[-1][1])

    # Cuts strictly inside an occupied interval split it; cuts elsewhere are
    # already segment boundaries (or fall in black and are meaningless).
    def strictly_inside(f):
        return any(s < f < e for s, e in occupied)

    segments = []
    pos = 0
    for s, e in occupied:
        if pos < s:
            segments.append(('gap', pos, s))
        interior = sorted(f for f in all_cuts if s < f < e)
        edges = [s] + interior + [e]
        for a, b in zip(edges, edges[1:]):
            segments.append(('clip', a, b))
        pos = e
    if pos < duration:
        segments.append(('gap', pos, duration))

    # Keep transitions only at actual segment boundaries; clamp offsets to the
    # adjacent segment durations.
    boundaries = {}
    for i in range(1, len(segments)):
        boundaries[segments[i][1]] = (segments[i - 1], segments[i])

    transitions = {}
    for cut, (in_off, out_off) in all_transitions.items():
        if cut not in boundaries:
            warn("WARNING: transition at frame %d is not at an edit point "
                 "(covered by another track?) - dropped" % cut)
            continue
        before, after = boundaries[cut]
        max_in = before[2] - before[1]
        max_out = after[2] - after[1]
        if in_off > max_in or out_off > max_out:
            warn("WARNING: transition at frame %d longer than adjacent segment - clamped" % cut)
            in_off = min(in_off, max_in)
            out_off = min(out_off, max_out)
        if in_off + out_off > 0:
            transitions[cut] = (in_off, out_off)

    return segments, transitions


# ---------------------------------------------------------------------------
# OTIO JSON construction (stdlib only - no opentimelineio package required)
# ---------------------------------------------------------------------------

def _rt(value, rate):
    return {"OTIO_SCHEMA": "RationalTime.1", "rate": float(rate), "value": float(value)}


def _time_range(start, duration, rate):
    return {"OTIO_SCHEMA": "TimeRange.1",
            "start_time": _rt(start, rate), "duration": _rt(duration, rate)}


def _otio_clip(name, file_path, avail_start, avail_duration, src_start, src_duration, rate):
    # Resolve exports (and relinks against) plain filesystem paths in
    # target_url, not file:// URIs.
    return {
        "OTIO_SCHEMA": "Clip.2",
        "metadata": {},
        "name": name,
        "source_range": _time_range(src_start, src_duration, rate),
        "effects": [],
        "markers": [],
        "enabled": True,
        "media_references": {
            "DEFAULT_MEDIA": {
                "OTIO_SCHEMA": "ExternalReference.1",
                "metadata": {},
                "name": name,
                "available_range": _time_range(avail_start, avail_duration, rate),
                "available_image_bounds": None,
                "target_url": file_path,
            }
        },
        "active_media_reference_key": "DEFAULT_MEDIA",
    }


def _otio_gap(duration, rate):
    return {"OTIO_SCHEMA": "Gap.1", "metadata": {}, "name": "",
            "source_range": _time_range(0, duration, rate),
            "effects": [], "markers": [], "enabled": True}


def _otio_transition(in_off, out_off, rate):
    return {"OTIO_SCHEMA": "Transition.1", "metadata": {},
            "name": "Cross Dissolve", "transition_type": "SMPTE_Dissolve",
            "in_offset": _rt(in_off, rate), "out_offset": _rt(out_off, rate)}


def build_otio_timeline(segments, transitions, clip_info, timeline_name):
    """Assemble the notched timeline as an OTIO JSON dict.

    Sequence frame f maps to media frame clip_info['start_frame'] + f, so
    every segment lands at its original source timecode.
    """
    rate = exact_rate(clip_info['fps'])
    start_frame = clip_info['start_frame']

    children = []
    for kind, a, b in segments:
        if transitions.get(a) and children:
            in_off, out_off = transitions[a]
            children.append(_otio_transition(in_off, out_off, rate))
        if kind == 'gap':
            children.append(_otio_gap(b - a, rate))
        else:
            children.append(_otio_clip(
                "%s [%d-%d]" % (clip_info['name'], a, b),
                clip_info['file_path'],
                start_frame, clip_info['frames'],
                start_frame + a, b - a, rate))

    return {
        "OTIO_SCHEMA": "Timeline.1",
        "metadata": {},
        "name": timeline_name,
        "global_start_time": _rt(start_frame, rate),
        "tracks": {
            "OTIO_SCHEMA": "Stack.1",
            "metadata": {},
            "name": "tracks",
            "source_range": None,
            "effects": [],
            "markers": [],
            "enabled": True,
            "children": [{
                "OTIO_SCHEMA": "Track.1",
                "metadata": {},
                "name": "V1",
                "source_range": None,
                "effects": [],
                "markers": [],
                "enabled": True,
                "children": children,
                "kind": "Video",
            }],
        },
    }


def unique_timeline_name(name, existing):
    """Return name unchanged if free, else with a trailing number incremented
    (or appended) until it doesn't collide with the names in existing."""
    if name not in existing:
        return name
    m = re.match(r'^(.*?)(\d+)$', name)
    if m:
        base, num, width = m.group(1), int(m.group(2)), len(m.group(2))
    else:
        base, num, width = name + ' ', 1, 0
    while True:
        num += 1
        candidate = base + str(num).zfill(width)
        if candidate not in existing:
            return candidate


# ---------------------------------------------------------------------------
# Resolve bootstrap (standard repo pattern)
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
# UI
# ---------------------------------------------------------------------------

def show_message(ui, dispatcher, title, text):
    win = dispatcher.AddWindow(
        {'ID': 'MsgDialog', 'WindowTitle': title, 'Geometry': [700, 300, 460, 110]},
        ui.VGroup({'Spacing': 8}, [
            ui.Label({'Text': text, 'WordWrap': True}),
            ui.HGroup({'Spacing': 6}, [
                ui.HGap(),
                ui.Button({'ID': 'OKBtn', 'Text': 'OK', 'Weight': 0}),
            ]),
        ])
    )

    def OnDone(ev):
        dispatcher.ExitLoop()

    win.On['MsgDialog'].Close = OnDone
    win.On['OKBtn'].Clicked = OnDone
    win.Show()
    dispatcher.RunLoop()
    win.Hide()


def run_dialog(fusion, ui, dispatcher, clip_info):
    """Main dialog: XML path + timeline name. Returns dict or None on cancel."""
    result = {'confirmed': False, 'xml_path': None, 'timeline_name': None,
              'all_as_cuts': False, 'edge_as_cuts': False}

    win = dispatcher.AddWindow(
        {'ID': 'NotchDialog', 'WindowTitle': 'RL XML NOTCH', 'Geometry': [700, 300, 560, 210]},
        ui.VGroup({'Spacing': 8}, [
            ui.Label({'Text': "Baked clip:  %s   (%s @ %s)" % (
                clip_info['name'], clip_info['start_tc'], clip_info['fps']), 'Weight': 0}),
            ui.HGroup({'Spacing': 6}, [
                ui.Label({'Text': 'Premiere XML:', 'Weight': 0}),
                ui.LineEdit({'ID': 'XMLPath', 'PlaceholderText': '/path/to/sequence.xml', 'Weight': 1}),
                ui.Button({'ID': 'BrowseBtn', 'Text': 'Browse...', 'Weight': 0}),
            ]),
            ui.HGroup({'Spacing': 6}, [
                ui.Label({'Text': 'Timeline name:', 'Weight': 0}),
                ui.LineEdit({'ID': 'NameInput', 'Text': clip_info['name'] + ' NOTCHED', 'Weight': 1}),
            ]),
            ui.CheckBox({'ID': 'AllCuts', 'Text': 'Treat all transitions as cuts (cut at transition center)', 'Weight': 0}),
            ui.CheckBox({'ID': 'EdgeCuts', 'Text': 'Treat edge transitions as cuts (fades to/from black become cuts)', 'Weight': 0}),
            ui.HGroup({'Spacing': 6}, [
                ui.HGap(),
                ui.Button({'ID': 'CancelBtn', 'Text': 'Cancel', 'Weight': 0}),
                ui.Button({'ID': 'OKBtn', 'Text': 'OK', 'Weight': 0}),
            ]),
        ])
    )

    itm = win.GetItems()

    def OnBrowse(ev):
        try:
            sel = fusion.RequestFile()
            if sel:
                itm['XMLPath'].Text = str(sel)
        except Exception as ex:
            print("File browser unavailable (%s) - paste the XML path instead." % ex)

    def OnOK(ev):
        path = (itm['XMLPath'].Text or '').strip()
        if not os.path.isfile(path):
            print("Not a file: %r - choose a valid XML file." % path)
            return
        result['xml_path'] = path
        result['timeline_name'] = (itm['NameInput'].Text or '').strip() or clip_info['name'] + ' NOTCHED'
        result['all_as_cuts'] = bool(itm['AllCuts'].Checked)
        result['edge_as_cuts'] = bool(itm['EdgeCuts'].Checked)
        result['confirmed'] = True
        dispatcher.ExitLoop()

    def OnCancel(ev):
        dispatcher.ExitLoop()

    win.On['NotchDialog'].Close = OnCancel
    win.On['BrowseBtn'].Clicked = OnBrowse
    win.On['OKBtn'].Clicked = OnOK
    win.On['CancelBtn'].Clicked = OnCancel

    win.Show()
    dispatcher.RunLoop()
    win.Hide()

    return result if result['confirmed'] else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def get_selected_clip(mediapool):
    try:
        selected = mediapool.GetSelectedClips()
    except (AttributeError, TypeError):
        return None, "GetSelectedClips is unavailable - Resolve 18.5 or newer is required."
    if not selected:
        return None, "Select the baked clip in the Media Pool first."
    clips = list(selected.values()) if isinstance(selected, dict) else list(selected)
    if len(clips) > 1:
        print("WARNING: %d clips selected - using the first." % len(clips))
    clip = clips[0]
    if clip.GetClipProperty('Type') == 'Timeline':
        return None, "The selected item is a timeline - select the baked media clip."
    return clip, None


def get_clip_info(clip):
    props = clip.GetClipProperty()
    fps = float(props['FPS'])
    start_tc = props['Start TC']
    file_path = props['File Path']
    if not file_path:
        return None, "The selected clip has no file path - select a disk-based media clip."
    return {
        'name': props['Clip Name'],
        'file_path': file_path,
        'fps': fps,
        'start_tc': start_tc,
        'frames': int(props['Frames']),
        'drop_frame': ';' in start_tc,
        'start_frame': tc_to_frames(start_tc, fps),
    }, None


def main():
    bmd = GetBmd()
    resolve = bmd.scriptapp("Resolve")
    fusion = resolve.Fusion()
    ui = fusion.UIManager
    dispatcher = bmd.UIDispatcher(ui)

    def fail(text):
        print("ERROR: " + text)
        show_message(ui, dispatcher, 'RL XML NOTCH', text)
        sys.exit()

    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        fail("No project is open.")
    mediapool = project.GetMediaPool()

    clip, err = get_selected_clip(mediapool)
    if err:
        fail(err)
    clip_info, err = get_clip_info(clip)
    if err:
        fail(err)
    print("Baked clip: %(name)s  %(start_tc)s @ %(fps)s, %(frames)d frames" % clip_info)

    choice = run_dialog(fusion, ui, dispatcher, clip_info)
    if not choice:
        print("Cancelled.")
        sys.exit()

    try:
        seq = parse_xmeml(choice['xml_path'])
    except (ET.ParseError, ValueError) as ex:
        fail("Could not read XML: %s" % ex)

    print("Sequence %r: %s tracks, timebase %d (%.3f fps), duration %d" % (
        seq['name'], len(seq['tracks']), seq['timebase'], seq['fps'], seq['duration']))

    if abs(seq['fps'] - clip_info['fps']) > 0.01:
        print("WARNING: XML rate (%.3f) differs from clip rate (%.3f) - cut frames "
              "are used as-is; verify the result." % (seq['fps'], clip_info['fps']))

    if choice['all_as_cuts']:
        print("Option: treating ALL transitions as cuts (centered in the transition span).")
    elif choice['edge_as_cuts']:
        print("Option: treating edge transitions (fades to/from black) as cuts.")

    try:
        segments, transitions = build_cutlist(
            seq['tracks'], seq['duration'],
            choice['all_as_cuts'], choice['edge_as_cuts'])
    except ValueError as ex:
        fail(str(ex))

    n_clips = sum(1 for k, _, _ in segments if k == 'clip')
    n_gaps = sum(1 for k, _, _ in segments if k == 'gap')
    total = segments[-1][2]
    print("Notch plan: %d clip segments, %d black gaps, %d dissolves, %d frames total"
          % (n_clips, n_gaps, len(transitions), total))

    if total > clip_info['frames']:
        print("WARNING: XML sequence (%d frames) is longer than the baked clip (%d frames) - "
              "trailing segments will run past the end of the media."
              % (total, clip_info['frames']))

    existing = set()
    for i in range(1, project.GetTimelineCount() + 1):
        tl = project.GetTimelineByIndex(i)
        if tl:
            existing.add(tl.GetName())
    timeline_name = unique_timeline_name(choice['timeline_name'], existing)
    if timeline_name != choice['timeline_name']:
        print("Timeline %r already exists - using %r instead."
              % (choice['timeline_name'], timeline_name))

    otio_data = build_otio_timeline(segments, transitions, clip_info, timeline_name)
    fd, otio_path = tempfile.mkstemp(suffix='.otio', prefix='RL_XML_NOTCH_')
    os.close(fd)
    with open(otio_path, 'w') as f:
        json.dump(otio_data, f, indent=2)

    folder = mediapool.GetCurrentFolder()
    option_sets = [
        {'importSourceClips': False, 'sourceClipsFolders': [folder]},
        {'importSourceClips': False, 'sourceClipsPath': os.path.dirname(clip_info['file_path'])},
        {'importSourceClips': True},
    ]
    timeline = None
    for options in option_sets:
        options['timelineName'] = timeline_name
        timeline = mediapool.ImportTimelineFromFile(otio_path, options)
        if timeline:
            if options.get('importSourceClips'):
                print("WARNING: relink to the pool clip failed - media was re-imported.")
            break

    if not timeline:
        print("ERROR: import failed. The generated OTIO was kept for inspection: %s" % otio_path)
        show_message(ui, dispatcher, 'RL XML NOTCH',
                     "Timeline import failed. Generated OTIO kept at:\n" + otio_path)
        sys.exit()

    os.remove(otio_path)

    got_tc = timeline.GetStartTimecode()
    print("Created timeline %r - start TC %s (clip start TC %s)"
          % (timeline.GetName(), got_tc, clip_info['start_tc']))
    if got_tc != clip_info['start_tc']:
        print("WARNING: timeline start TC does not match the clip start TC.")
    print("Done.")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
