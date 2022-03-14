import os
import vlc
from tkinter import *
from tkinter.messagebox import showinfo
from tkinter import filedialog as fd
import tempfile
from spleeter.separator import Separator


class App:

  def __init__(self):
    self.is_playing = False
    self.song_loaded = False
    self.vocals_mp3, self.drums_mp3, self.bass_mp3, self.other_mp3 = None, None, None, None
    self.song_path = None
    self.tempdir = tempfile.mkdtemp(prefix="virtual_stem_player-")

    self.root = Tk()
    self.pause = Button(self.root, command=self.pause_and_play, state=DISABLED)
    self.vocals = Scale(self.root, from_=100, to=0, command=self.update_vocals)
    self.drums = Scale(self.root, from_=100, to=0, orient=HORIZONTAL, command=self.update_drums)
    self.bass = Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command=self.update_bass)
    self.other = Scale(self.root, from_=0, to=100, command=self.update_other)

    self.song_button = Button(self.root, text="Select Song",  command=self.select_song)

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
    self.song_button.place(x=10, y=10)

    self.root.title("Virtual Stem Player")
    self.root.geometry("300x300")
    self.root.resizable(False, False)
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
    
    cut = Separator('spleeter:4stems')
    split_path = self.song_path.split("/")
    song_name = split_path[len(split_path)-1].replace(".mp3", "")

    showinfo(
      title='Loading',
      message='Loading music, wait for success window.'
    )
    generated_path = self.tempdir + "/" + song_name
    if not (os.path.exists(generated_path)):
      cut.separate_to_file(self.song_path, self.tempdir, codec='mp3');
    self.vocals_mp3 = vlc.MediaPlayer(generated_path + "/vocals.mp3")
    self.drums_mp3 = vlc.MediaPlayer(generated_path + "/drums.mp3")
    self.bass_mp3 = vlc.MediaPlayer(generated_path + "/bass.mp3")
    self.other_mp3 = vlc.MediaPlayer(generated_path + "/other.mp3")
    self.song_loaded = True
    self.pause['state'] = NORMAL

    showinfo(
      title='Success',
      message='Music Loaded'
    )

  def select_song(self):
    self.song_loaded = False
    self.pause['state'] = DISABLED
    self.song_path = fd.askopenfilename(title='Choose a song',initialdir='/', filetypes=[("Mp3 Files", "*.mp3")])
    print(self.song_path)
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