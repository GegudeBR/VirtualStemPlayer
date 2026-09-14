import hashlib
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter.messagebox import showinfo

import vlc

STEMS = ("drums", "bass", "other", "vocals")
AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".mp4")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "virtual-stem-player")


def stem_dir_for(song_path):
  """Persistent output dir for a song, keyed by path + size + mtime.

  So picking the same song again skips re-separating it.
  """
  st = os.stat(song_path)
  digest = hashlib.sha256()
  digest.update(song_path.encode("utf-8", "replace"))
  digest.update(str(st.st_size).encode())
  digest.update(str(st.st_mtime_ns).encode())
  return os.path.join(CACHE_DIR, digest.hexdigest())


def existing_stem_files(output_dir):
  """Return {stem: path} if a previous split exists, else None."""
  files = {}
  for stem in STEMS:
    for ext in (".mp3", ".wav"):
      candidate = os.path.join(output_dir, stem + ext)
      if os.path.exists(candidate):
        files[stem] = candidate
        break
  return files if len(files) == len(STEMS) else None


class App:

  def __init__(self):
    self.root = tk.Tk()
    self.update_media = True
    self.is_playing = False
    self.song_loaded = False
    self.separator = None
    self.stem_players = {}
    self.song_path = None
    self.output_dir = None
    self.processing = None
    self._results = queue.Queue()
    self._audio_ready = False
    self._volumes = {stem: 100 for stem in STEMS}
    self.previous_vocals = 100

    # Applying theme (resolved relative to this file so it works from any cwd)
    libs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libs')
    self.root.tk.call('source', os.path.join(libs_dir, 'forest-dark.tcl'))
    ttk.Style().theme_use('forest-dark')

    # Defining elements
    self.pause = ttk.Button(self.root, text="Play", command=self.pause_and_play, state=tk.DISABLED)
    self.vocals = ttk.Scale(self.root, from_=100, to=0, orient=tk.VERTICAL, length=90,
                            command=self.update_vocals)
    self.drums = ttk.Scale(self.root, from_=100, to=0, orient=tk.HORIZONTAL, length=130,
                           command=self.update_drums)
    self.bass = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL, length=130,
                          command=self.update_bass)
    self.other = ttk.Scale(self.root, from_=0, to=100, orient=tk.VERTICAL, length=90,
                           command=self.update_other)
    self.media_time = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL)
    self.song_button = ttk.Button(self.root, text="Select Song", command=self.select_song)

    # Setting sliders to 100%
    self.set_max_stems()

    # Layout: stems arranged in a cross around a centered play button.
    self.root.columnconfigure(0, weight=1)
    self.root.columnconfigure(2, weight=1)

    self.song_button.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 2))

    ttk.Label(self.root, text="Vocals").grid(row=1, column=1, pady=(2, 0))
    self.vocals.grid(row=2, column=1, pady=(0, 2))

    ttk.Label(self.root, text="Drums").grid(row=3, column=0, sticky="w", padx=(12, 0))
    ttk.Label(self.root, text="Bass").grid(row=3, column=2, sticky="e", padx=(0, 12))
    self.drums.grid(row=4, column=0, padx=12, sticky="w")
    self.pause.grid(row=4, column=1, pady=(4, 0))
    self.bass.grid(row=4, column=2, padx=12, sticky="e")

    ttk.Label(self.root, text="Other").grid(row=5, column=1, pady=(2, 0))
    self.other.grid(row=6, column=1, pady=(0, 2))

    self.media_time.grid(row=7, column=0, columnspan=3, sticky="ew", padx=12, pady=(14, 18))

    # Binds
    self.root.bind('m', self.mute_vocals)
    self.media_time.bind('<ButtonRelease-1>', self.move_media)
    self.media_time.bind('<ButtonPress-1>', self.cancel_move_media)

    self.root.title("Virtual Stem Player")
    self.root.geometry("370x410")
    self.root.resizable(False, False)

    self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    self.root.after(50, self.update_media_time)
    self.root.mainloop()

  def cancel_move_media(self, _event):
    self.update_media = False

  def move_media(self, _event):
    target = int(self.media_time.get() * 1000)
    for player in self.stem_players.values():
      player.set_time(target)
    self.update_media = True

  def set_max_stems(self):
    for stem in (self.vocals, self.drums, self.bass, self.other):
      stem.set(100)

  def set_stem_volume(self, stem, volume):
    # Store the desired volume. Only push to libvlc once the audio output
    # exists; calling audio_set_volume before playback starts can crash the
    # VLC audio thread (observed with the PipeWire output).
    self._volumes[stem] = volume
    player = self.stem_players.get(stem)
    if player is not None and self._audio_ready:
      player.audio_set_volume(volume)

  def _apply_volumes(self):
    for stem, volume in self._volumes.items():
      player = self.stem_players.get(stem)
      if player is not None:
        player.audio_set_volume(volume)

  def update_vocals(self, _event):
    self.set_stem_volume("vocals", int(self.vocals.get()))

  def update_drums(self, _event):
    self.set_stem_volume("drums", int(self.drums.get()))

  def update_bass(self, _event):
    self.set_stem_volume("bass", int(self.bass.get()))

  def update_other(self, _event):
    self.set_stem_volume("other", int(self.other.get()))

  def mute_vocals(self, _event):
    if int(self.vocals.get()) > 0:
      self.previous_vocals = int(self.vocals.get())
      self.vocals.set(0)
    else:
      self.vocals.set(self.previous_vocals)

  def select_song(self):
    path = fd.askopenfilename(
      title='Choose a song',
      filetypes=[("Audio files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.mp4"), ("All files", "*.*")]
    )
    if not path or not os.path.isfile(path):
      return
    if not path.lower().endswith(AUDIO_EXTS):
      showinfo('Error!', 'Please choose a supported audio file.')
      return

    self.song_path = path
    self.song_loaded = False
    self.pause['text'] = "Processing..."
    self.pause['state'] = tk.DISABLED

    self.output_dir = stem_dir_for(path)
    os.makedirs(self.output_dir, exist_ok=True)

    cached = existing_stem_files(self.output_dir)
    if cached:
      # Stems already split: load instantly, skip the processing popup.
      self._on_split_done(cached)
      return

    self._show_processing()
    threading.Thread(target=self._separate_worker, daemon=True).start()

  def _show_processing(self):
    self.processing = tk.Toplevel(self.root)
    self.processing.title("Processing...")
    self.processing.resizable(False, False)
    self.processing.protocol("WM_DELETE_WINDOW", lambda: None)
    ttk.Label(
      self.processing,
      text="Processing...\nSplitting the song into stems, please wait.\nThis may take a few minutes on first use.",
      justify=tk.CENTER
    ).pack(padx=24, pady=24)
    self.processing.update_idletasks()
    x = self.root.winfo_rootx() + (self.root.winfo_width() - self.processing.winfo_reqwidth()) // 2
    y = self.root.winfo_rooty() + (self.root.winfo_height() - self.processing.winfo_reqheight()) // 2
    self.processing.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    self.processing.transient(self.root)
    self.processing.grab_set()

  def _hide_processing(self):
    if self.processing is not None:
      self.processing.destroy()
      self.processing = None

  def _separate_worker(self):
    # Background thread: never touch tkinter here. Results are handed back
    # via a queue that the main loop drains in update_media_time().
    try:
      files = self.separate_song(self.song_path, self.output_dir)
    except Exception as exc:
      self._results.put(("error", str(exc)))
      return
    self._results.put(("done", files))

  def _dispatch_results(self):
    while True:
      try:
        kind, payload = self._results.get_nowait()
      except queue.Empty:
        break
      if kind == "done":
        self._on_split_done(payload)
      else:
        self._on_split_error(payload)

  def _on_split_done(self, files):
    self._hide_processing()
    for stem, path in files.items():
      self.stem_players[stem] = vlc.MediaPlayer(path)
    self.set_max_stems()
    self.song_loaded = True
    self.pause['text'] = "Play"
    self.pause['state'] = tk.NORMAL
    showinfo('Success', 'Music loaded!')

  def _on_split_error(self, message):
    self._hide_processing()
    self.pause['text'] = "Play"
    self.pause['state'] = tk.DISABLED
    showinfo('Error!', 'Could not split the song:\n' + message)

  def separate_song(self, song_path, output_dir):
    # Lazy import so the UI opens instantly; torch/demucs take a few seconds to load.
    from demucs.api import Separator
    from demucs.audio import save_audio

    if self.separator is None:
      self.separator = Separator('htdemucs')

    os.makedirs(output_dir, exist_ok=True)
    _, separated = self.separator.separate_audio_file(song_path)

    # Stem order for htdemucs is (drums, bass, other, vocals).
    files = {}
    for stem in STEMS:
      path = os.path.join(output_dir, stem + ".mp3")
      try:
        save_audio(separated[stem], path, samplerate=self.separator.samplerate, bitrate=320)
      except Exception:
        path = os.path.join(output_dir, stem + ".wav")
        save_audio(separated[stem], path, samplerate=self.separator.samplerate)
      files[stem] = path
    print("Stems saved to:", output_dir)
    return files

  def update_media_time(self):
    self._dispatch_results()
    if self.stem_players and not self._audio_ready:
      player = self.stem_players.get("vocals")
      if player is not None and player.get_state() == vlc.State.Playing:
        self._audio_ready = True
        self._apply_volumes()
    player = self.stem_players.get("vocals")
    if player is not None and self.update_media:
      length = player.get_length() / 1000
      if length > 0 and self.media_time['to'] != length:
        self.media_time['to'] = length
      self.media_time.set(player.get_time() / 1000)
    self.root.after(50, self.update_media_time)

  def on_close(self):
    for player in self.stem_players.values():
      player.stop()
    self.root.destroy()

  def pause_and_play(self):
    if not self.song_loaded:
      showinfo('Error!', 'Load a song first!')
      return
    if not self.is_playing:
      for player in self.stem_players.values():
        player.play()
      self.pause['text'] = "Pause"
    else:
      for player in self.stem_players.values():
        player.pause()
      self.pause['text'] = "Play"
    self.is_playing = not self.is_playing


if __name__ == "__main__":
  App()