import os
import vlc
from tkinter import *
import tempfile
from spleeter.separator import Separator


class App:

  def __init__(self):
    self.is_playing = False
    self.song_loaded = False
    self.vocals_mp3, self.drums_mp3, self.bass_mp3, self.other_mp3 = None, None, None, None
    self.root = Tk()
    self.pause = Button(self.root, command=self.pause_and_play)
    self.vocals = Scale(self.root, from_=100, to=0, command=self.update_vocals)
    self.drums = Scale(self.root, from_=100, to=0, orient=HORIZONTAL, command=self.update_drums)
    self.bass = Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command=self.update_bass)
    self.other = Scale(self.root, from_=0, to=100, command=self.update_other)

    allStems = [self.vocals, self.drums, self.bass, self.other]

    for stem in allStems:
      stem.set(100)

    center_x = 110

    # Top Mid
    self.vocals.place(x=center_x, y=10)  
    # Mid Left
    self.drums.place(x=10, y=120)
    #Mid Right
    self.bass.place(x=190, y=120)
    #Bottom Mid
    self.other.place(x=center_x,y=180)

    self.pause.place(x=center_x + 25,y=130,height=30, width=30)

    self.root.title("Virtual Stem Player")
    self.root.geometry("300x300")
    self.root.resizable(False, False)
    self.setup()
    self.root.mainloop()

  def update_vocals(self, event):
    if self.vocals_mp3 != None:
      self.vocals_mp3.audio_set_volume(self.vocals.get()) 
  def update_drums(self, event):
    if self.drums_mp3 != None:
      self.drums_mp3.audio_set_volume(self.drums.get()) 
  def update_bass(self, event):
    if self.bass_mp3 != None:
      self.bass_mp3.audio_set_volume(self.bass.get()) 
  def update_other(self, event):
    if self.other_mp3 != None:
      self.other_mp3.audio_set_volume(self.other.get()) 

  def setup(self):
    #tempdir = tempfile.mkdtemp(prefix="virtual_stem_player-")
    #cut = Separator('spleeter:4stems')
    tempdir = "/Users/hallaig/Desktop"
    input_path = "/Users/hallaig/Desktop/Happier_Than_ever.mp3"
    split_path = input_path.split("/")
    song_name = split_path[len(split_path)-1].replace(".mp3", "")
    #cut.separate_to_file(input_path, tempdir);
    self.vocals_mp3 = vlc.MediaPlayer(tempdir + "/" + song_name + "/vocals.mp3")
    self.drums_mp3 = vlc.MediaPlayer(tempdir + "/" + song_name + "/drums.mp3")
    self.bass_mp3 = vlc.MediaPlayer(tempdir + "/" + song_name + "/bass.mp3")
    self.other_mp3 = vlc.MediaPlayer(tempdir + "/" + song_name + "/other.mp3")
    self.song_loaded = True
    

  def pause_and_play(self):
    if not self.song_loaded:
      return
    if not self.is_playing: 
      self.vocals_mp3.play()
      self.drums_mp3.play()
      self.bass_mp3.play()
      self.other_mp3.play()
    else:
      self.vocals_mp3.stop()
      self.drums_mp3.stop()
      self.bass_mp3.stop()
      self.other_mp3.stop()

    self.is_playing = not self.is_playing

app=App()