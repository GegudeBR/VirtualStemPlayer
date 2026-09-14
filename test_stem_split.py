"""Tests for StemPlayer's stem-splitting functions.

Fast tests (path/cache helpers) run on every invocation. The full Demucs
separation against the bundled example song is slow (minutes on CPU), so it
only runs when STEM_TEST_RUN_SLOW=1:

    STEM_TEST_RUN_SLOW=1 .venv/bin/python -m unittest test_stem_split -v
"""
import math
import os
import struct
import sys
import tempfile
import time
import unittest
import wave

import vlc

import StemPlayer as stem

EXAMPLE_SONG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "example",
    "15 - Happier Than Ever.flac",
)
RUN_SLOW = os.environ.get("STEM_TEST_RUN_SLOW", "").lower() in ("1", "true", "yes")


def _write_tiny_wav(path, seconds=1.0, rate=16000):
    magnitude = int(seconds * rate)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(magnitude):
            sample = int(8000 * math.sin(2 * math.pi * 440 * i / rate))
            frames += struct.pack("<hh", sample, sample)
        w.writeframes(bytes(frames))


class StemDirTests(unittest.TestCase):

  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()

  def tearDown(self):
    self.tmp.cleanup()

  def _make_song(self, name, seconds=1.0):
    path = os.path.join(self.tmp.name, name)
    _write_tiny_wav(path, seconds)
    return path

  def test_dir_is_deterministic(self):
    song = self._make_song("a.wav")
    self.assertEqual(stem.stem_dir_for(song), stem.stem_dir_for(song))

  def test_dir_changes_with_file(self):
    song_a = self._make_song("a.wav", 1.0)
    song_b = self._make_song("b.wav", 2.0)
    self.assertNotEqual(stem.stem_dir_for(song_a), stem.stem_dir_for(song_b))

  def test_existing_stem_files_none_when_empty(self):
    empty = os.path.join(self.tmp.name, "empty")
    os.makedirs(empty)
    self.assertIsNone(stem.existing_stem_files(empty))

  def test_existing_stem_files_finds_complete_split(self):
    out = os.path.join(self.tmp.name, "out")
    os.makedirs(out)
    expected = {}
    for s in stem.STEMS:
      path = os.path.join(out, s + ".mp3")
      open(path, "w").close()
      expected[s] = path
    files = stem.existing_stem_files(out)
    self.assertIsNotNone(files)
    self.assertEqual(sorted(files), sorted(expected))
    self.assertEqual(set(files.values()), set(expected.values()))

  def test_existing_stem_files_ignores_partial_split(self):
    out = os.path.join(self.tmp.name, "out")
    os.makedirs(out)
    open(os.path.join(out, "vocals.mp3"), "w").close()
    self.assertIsNone(stem.existing_stem_files(out))

  def test_existing_stem_files_prefers_mp3_over_wav(self):
    out = os.path.join(self.tmp.name, "out")
    os.makedirs(out)
    for s in stem.STEMS:
      open(os.path.join(out, s + ".wav"), "w").close()
      open(os.path.join(out, s + ".mp3"), "w").close()
    files = stem.existing_stem_files(out)
    self.assertTrue(all(path.endswith(".mp3") for path in files.values()))


@unittest.skipUnless(os.path.isfile(EXAMPLE_SONG), "example song not present")
@unittest.skipUnless(RUN_SLOW, "set STEM_TEST_RUN_SLOW=1 to run Demucs separation")
class SplitExampleSongTests(unittest.TestCase):

  def _assert_playable(self, path):
    player = vlc.MediaPlayer(path)
    try:
      player.play()
      time.sleep(1.2)
      self.assertEqual(player.get_state(), vlc.State.Playing)
      self.assertGreater(player.get_length(), 0)
    finally:
      player.stop()
      player.release()

  def test_separate_song_splits_example(self):
    app = stem.App.__new__(stem.App)
    app.separator = None
    out = stem.stem_dir_for(EXAMPLE_SONG)
    os.makedirs(out, exist_ok=True)

    start = time.time()
    files = app.separate_song(EXAMPLE_SONG, out)
    elapsed = time.time() - start
    print(f"\nseparation took {elapsed:.1f}s -> {out}", file=sys.stderr)

    self.assertEqual(sorted(files), sorted(stem.STEMS))
    for s in stem.STEMS:
      with self.subTest(stem=s):
        path = files[s]
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)
        self._assert_playable(path)

    # The output dir must now be reusable by later app launches,
    # skipping demucs entirely (the cache-hit path).
    cached = stem.existing_stem_files(out)
    self.assertEqual(sorted(cached or {}), sorted(files))


if __name__ == "__main__":
  unittest.main()