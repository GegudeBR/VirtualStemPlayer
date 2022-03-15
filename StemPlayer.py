import os
import vlc
from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
from tkinter import filedialog as fd
import tempfile
from spleeter.separator import Separator


class App:

  def __init__(self):
    self.root = Tk()

    # Applying Themes
    self.root.tk.call('source', 'libs/forest-dark.tcl')
    ttk.Style().theme_use('forest-dark')


    # Defining variablesm
    self.is_playing = False
    self.song_loaded = False
    self.vocals_mp3, self.drums_mp3, self.bass_mp3, self.other_mp3 = None, None, None, None
    self.previous_vocals = 0
    self.song_path = None
    self.tempdir = tempfile.mkdtemp(prefix="virtual_stem_player-")

    # Defining Elements
    self.pause = ttk.Button(self.root, command=self.pause_and_play, state=DISABLED)
    self.vocals = ttk.Scale(self.root, from_=100, to=0, orient=VERTICAL, command=self.update_vocals)
    self.drums = ttk.Scale(self.root, from_=100, to=0, orient=HORIZONTAL, command=self.update_drums)
    self.bass = ttk.Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command=self.update_bass)
    self.other = ttk.Scale(self.root, from_=0, to=100, orient=VERTICAL, command=self.update_other)
    self.media_time = ttk.Scale(self.root, from_=0, to=100, length=280, orient=HORIZONTAL)
    self.song_button = ttk.Button(self.root, text="Select Song",  command=self.select_song)

    # Setting sliders to 100%
    self.set_max_stems()

    center_x = 140
    center_y = 130

    # Top Mid
    self.vocals.place(x=center_x, y=10)  
    # Mid Left
    self.drums.place(x=10, y=center_y)
    #Mid Right
    self.bass.place(x=190, y=center_y)
    #Bottom Mid
    self.other.place(x=center_x,y=170)

    self.pause.place(x=center_x - 5, y=center_y - 5,height=30, width=30)
    self.song_button.place(x=10, y=10)

    self.media_time.place(x=10, y=280)

    # Binds
    self.root.bind('m', self.mute_vocals)


    self.root.title("Virtual Stem Player")
    self.root.geometry("300x300")
    self.root.resizable(False, False)
    while(1):
      if self.vocals_mp3 != None:
        if self.media_time['to'] != (self.vocals_mp3.get_length() / 1000):
          self.media_time['to'] = self.vocals_mp3.get_length() / 1000
        #print(self.vocals_mp3.get_time() / 1000)
        self.media_time.set(self.vocals_mp3.get_time() / 1000)
      self.root.update_idletasks()
      self.root.update()

  def move_media(self, event):
    if self.vocals_mp3 != None:
      stems = [self.vocals_mp3, self.drums_mp3, self.bass_mp3, self.other_mp3]
      for stem in stems:
        stem.set_time(int(self.media_time.get() * 1000))

  def set_max_stems(self):
    stems = [self.vocals, self.drums, self.bass, self.other]
    for stem in stems:
      stem.set(100)

  def mute_vocals(self, event):
    if int(self.vocals.get()) > 0:
      self.previous_vocals = int(self.vocals.get())
      self.vocals.set(0)
    else: 
      self.vocals.set(self.previous_vocals)
      
  def update_vocals(self, event):
    if self.vocals_mp3 != None:
      self.vocals_mp3.audio_set_volume(int(self.vocals.get())) 

  def update_drums(self, event):
    if self.drums_mp3 != None:
      self.drums_mp3.audio_set_volume(int(self.drums.get()))  
  def update_bass(self, event):
    if self.bass_mp3 != None:
      self.bass_mp3.audio_set_volume(int(self.bass.get())) 
  def update_other(self, event):
    if self.other_mp3 != None:
      self.other_mp3.audio_set_volume(int(self.other.get())) 

  def setup(self):
    #cut = Separator('spleeter:4stems')
    #split_path = self.song_path.split("/")
    #song_name = split_path[len(split_path)-1].replace(".mp3", "")

    showinfo(
      title='Loading',
      message='Loading music, wait for success window.'
    )

    #generated_path = self.tempdir + "/" + song_name
    generated_path = "/Users/hallaig/Desktop/Happier_Than_ever"
    #if not (os.path.exists(generated_path)):
    #  cut.separate_to_file(self.song_path, self.tempdir, codec='mp3');
    self.vocals_mp3 = vlc.MediaPlayer(generated_path + "/vocals.mp3")
    self.drums_mp3 = vlc.MediaPlayer(generated_path + "/drums.mp3")
    self.bass_mp3 = vlc.MediaPlayer(generated_path + "/bass.mp3")
    self.other_mp3 = vlc.MediaPlayer(generated_path + "/other.mp3")

    self.set_max_stems()
    self.song_loaded = True
    self.pause['state'] = NORMAL

    showinfo(
      title='Success',
      message='Music loaded!'
    )

  def select_song(self):
    self.song_loaded = False
    self.pause['state'] = DISABLED
    self.song_path = fd.askopenfilename(title='Choose a song',initialdir='/', filetypes=[("Mp3 Files", "*.mp3")])
    '''
    showinfo(
      title='Selected Song',
      message=self.song_path
    )
    '''

    if ".mp3" in self.song_path:
      self.setup()
    

  def pause_and_play(self):
    if not self.song_loaded:
      showinfo(
        title='Error!',
        message='Load a music first!'
      )
      return
    if not self.is_playing: 
      self.vocals_mp3.play()
      self.drums_mp3.play()
      self.bass_mp3.play()
      self.other_mp3.play()
    else:
      self.vocals_mp3.pause()
      self.drums_mp3.pause()
      self.bass_mp3.pause()
      self.other_mp3.pause()

    self.is_playing = not self.is_playing

if __name__ == "__main__":
  app=App()