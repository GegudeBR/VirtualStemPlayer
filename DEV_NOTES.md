# VirtualStemPlayer — Developer Guide

Notes for anyone picking up this project later. It's a small Tkinter app that
splits a song into 4 stems (vocals, drums, bass, other) with Demucs and plays
the stems simultaneously with python-vlc, letting you solo/mute individual
instruments.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt   # demucs, python-vlc
.venv/bin/python StemPlayer.py
```

- Torch is installed from the CPU index first so `pip install demucs` does not
  pull the 2.5 GB CUDA build.
- Requires VLC's `libvlc` on the system (python-vlc is just a ctypes wrapper).
- First run downloads the `htdemucs` model (~84 MB) into
  `~/.cache/huggingface/hub` — this only happens once and is cached from then on.

## How the app works

```
Select Song ──> select_song()
                   │
                   ├─ compute cache dir (stem_dir_for)
                   ├─ cached stems present?  ──YES──▶ _on_split_done()  (instant, no popup)
                   │
                   └─ NO: show "Processing..." popup
                        └─ spawn worker thread → separate_song()
                             │   (demucs runs here; NO tkinter calls from this thread)
                             │
                             └─ put ("done"/"error", payload) on queue.Queue
                                  └─ main-loop poll (update_media_time, every 50ms)
                                       └─ _dispatch_results() → _on_split_done() / _on_split_error()
                                            ├─ creates vlc.MediaPlayer per stem (MAIN thread)
                                            └─ enables Play button
```

### Threading rules (important)

- The Demucs split runs in a `threading.Thread`. tkinter is **not**
  thread-safe: the worker never touches `self.root` or any widget.
- Results are passed back through `self._results` (`queue.Queue`) and drained
  in `update_media_time()`, which is scheduled on the main loop via
  `root.after(50, ...)`.
- All `vlc.MediaPlayer` creation and playback happens on the main thread.
- A previous bug called `root.after()` from the worker thread; that raised
  `RuntimeError: main thread is not in main loop` and corrupted tkinter,
  which preceded the segfault. Do not reintroduce cross-thread tkinter calls.

### Stem output / caching

- Output goes to `~/.cache/virtual-stem-player/<sha256>/` where the hash is
  derived from the song's **path + size + mtime** (`stem_dir_for`,
  `StemPlayer.py`). Stable across runs → picking the same song again is
  instant (cache hit skips Demucs entirely, with no "Processing..." popup).
- Files are `<stem>.mp3` (320 kbps), falling back to `<stem>.wav` if the MP3
  encoder is unavailable. `existing_stem_files()` prefers `.mp3` over `.wav`.
- `htdemucs` stem names/order: `drums, bass, other, vocals` — `STEMS` tuple.
- Old runs used a per-launch `tempfile.mkdtemp`, so every launch re-separated
  the song. Caching removed that.

### Volume handling

- Slider values are stored in `self._volumes` immediately.
- They are only pushed to libvlc (`audio_set_volume`) after `self._audio_ready`
  becomes true, which happens when playback is confirmed running
  (`vlc.State.Playing` in `update_media_time`).
- Calling `audio_set_volume` before playback starts is suspected of crashing
  VLC's audio thread (see Known issue).

### UI layout

- 370x410, `resizable(False, False)`, forest-dark ttk theme.
- Uses `grid` (not the old hardcoded `place()` coordinates): a cross
  arrangement with the play button centered —

  ```
  Select Song
       Vocals (V)
  Drums (H)  [Play]  Bass (H)
       Other (V)
  [=========== timeline ===========]
  ```
- Stem sliders have `ttk.Label` captions. The timeline spans the full width
  (`sticky="ew"`). Columns 0 and 2 share weight so the layout centers.

## Files

| File                      | Purpose                                             |
|---------------------------|-----------------------------------------------------|
| `StemPlayer.py`           | The whole app (UI + split + playback)               |
| `test_stem_split.py`      | Unit + integration tests for the split functions    |
| `requirements.txt`        | `demucs`, `python-vlc`                              |
| `libs/forest-*.tcl`       | ttk themes (patched to accept Tk 9.0)               |
| `example/*.flac`          | Local test song (gitignored? — check `git status`)  |
| `images/UI.png`           | README screenshot                                   |

`electron/` was a half-finished Electron port; it was deleted (see git
history) — Demucs is the backend either way, so a non-Tk UI added only
footprint with no benefit.

## Tests

```bash
# Fast tests (cache dir determinism, existing_stem_files logic) — always run
.venv/bin/python -m unittest test_stem_split -v

# Slow integration: full Demucs split of example/15 - Happier Than Ever.flac
STEM_TEST_RUN_SLOW=1 .venv/bin/python -m unittest test_stem_split -v
```

The slow test runs `separate_song()` for real and asserts each stem file is
non-empty and actually playable by VLC (state becomes `Playing`, length > 0;
VLC reports length only after play() starts). On CPU a full song takes ~4 min.

## Known issue: intermittent segfault during playback

Status: **not reproduced in normal app use** as of the last session — playback
has been stable. The fix that removed the guaranteed crash is the deferred
volume application (see below). A synthetic harness (`/tmp/opencode/repro.py`,
which replaces the real mainloop with a manual `update()` pump) can still crash
intermittently, so the underlying race is presumed not fully closed — if you
see a crash, start here. Keep this section in mind but don't assume a bug until
reproduced with the real mainloop.

### Evidence

Faulthandler C-stack (most recent first) from a crash:

```
libpipewire-0.3.so   pw_thread_loop_lock
vlc/.../libaout_pipewire_plugin.so
libvlccore.so        aout_VolumeSet
libvlc.so            libvlc_audio_set_volume
_ctypes              (python-vlc introspecting the audio_set_volume libvlc export)
```

i.e. the crash is inside **VLC's PipeWire audio output** during
`libvlc_audio_set_volume`. It did not happen on an earlier Tk/Tk-8.6 setup.

### Environment

- Python 3.14, python-vlc 3.0.21203, VLC 3.0.23 (distro build), PipeWire audio
- Crash frequency observed with the repro: ~intermittent (e.g. 1 of 3 runs)

### What's been done

- Volume application deferred until `vlc.State.Playing` (`_audio_ready` /
  `_apply_volumes`). This removed the guaranteed crash at load time but the
  race is still reachable: `get_state() == Playing` can be true while the
  PipeWire thread is still coming up.
- Worker-thread tkinter calls removed (fixed the non-libvlc half of the crash).

### Hypotheses / next steps for a future agent

1. **Force a different audio output** to test association, e.g. create a
   single shared libvlc instance:
   `vlc.Instance(["--aout=pulse"])` or `["--aout=alsa"]` and build `MediaPlayer`
   off that instance. If it stops crashing, the PipeWire plugin is the trigger.
2. **Push volume less aggressively**: drop `audio_set_volume` entirely and rely
   on the audit mixer, or apply volumes only on `libvlc_AudioPlay`/state-change
   events via `event_manager` rather than polling.
3. **Single shared LibVLC instance** for all four players (currently each
   `MediaPlayer(path)` uses the shared default instance — confirm, since
   python-vlc's default `Instance()` is global). A dedicated
   `vlc.Instance(["--no-video"])` may also reduce cross-audio-thread churn.
4. **Upgrade/downgrade VLC**: this looks like a VLC 3.0.x + PipeWire defect;
   test against VLC 4/next or `--aout=pipewire` explicit flags, and against
   `libvlc_audio_set_volume` before vs after `play()`.
5. If still unresolved, isolate playback to a subprocess (bundle the four stem
   tracks with ffmpeg into one file, or drive `cvlc` per player) so a libvlc
   crash cannot take the GUI down.