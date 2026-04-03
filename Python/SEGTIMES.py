import sys
import os
import platform
import subprocess

def add_resolve_path():
    if platform.system() == "Darwin":
        module_path = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
    elif platform.system() == "Windows":
        module_path = os.path.join(os.environ['PROGRAMDATA'], "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules")
    else:
        module_path = "/opt/resolve/libs/Fusion/Modules/"
    if module_path not in sys.path:
        sys.path.append(module_path)

add_resolve_path()

def copy_to_clipboard(text):
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run("clip", text=True, input=text, check=True)
        elif system == "Darwin":
            subprocess.run("pbcopy", text=True, input=text, check=True)
        elif system == "Linux":
            subprocess.run("xclip -selection clipboard", shell=True, text=True, input=text, check=True)
        else:
            print("Clipboard copy not supported on this OS.")
    except Exception as e:
        print(f"Failed to copy to clipboard: {e}")

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


try:
    import DaVinciResolveScript as dvr_script
except ImportError:
    print("Could not import DaVinciResolveScript.")
    sys.exit()

resolve   = dvr_script.scriptapp("Resolve")
project   = resolve.GetProjectManager().GetCurrentProject()
timeline  = project.GetCurrentTimeline() if project else None

if not timeline:
    print("No active timeline.")
    sys.exit()

# Get timeline frame rate and drop frame setting
fps_str        = timeline.GetSetting("timelineFrameRate")
drop_frame_str = timeline.GetSetting("timelineDropFrameTimecode")

fps        = float(fps_str)
drop_frame = (str(drop_frame_str) == "1")

# Get In/Out points (values are frame offsets from timeline origin)
inout          = timeline.GetMarkInOut()
timeline_start = timeline.GetStartFrame()

in_offset  = inout.get("video", {}).get("in")
out_offset = inout.get("video", {}).get("out")

if in_offset is None or out_offset is None or in_offset < 0 or out_offset < 0:
    print("No In/Out points set on timeline.")
    sys.exit()

in_frame  = in_offset  + timeline_start
out_frame = out_offset + timeline_start

duration_frames = out_frame - in_frame + 1

in_tc       = frames_to_timecode(in_frame,       fps, drop_frame)
out_tc      = frames_to_timecode(out_frame,      fps, drop_frame)
duration_tc = frames_to_timecode(duration_frames, fps, drop_frame)

output = f"{in_tc} - {out_tc}  TRT {duration_tc}"
print(output)
copy_to_clipboard(output)
