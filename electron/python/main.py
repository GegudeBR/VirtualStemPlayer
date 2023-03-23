import sys
import os
from spleeter.separator import Separator


if __name__ == "__main__":
  # Check if argument is provided
  if len(sys.argv) < 2:
    print('Please provide a song path')
    sys.exit(1)
  # Check if provided argument is a file
  if not os.path.isfile(sys.argv[1]):
    print('Please provide a valid song path')
    sys.exit(1)

  # Check if provided argument is a mp3 file
  if not sys.argv[1].endswith('.mp3'):
    print('Please provide a mp3 song')
    sys.exit(2)

  song_path = sys.argv[1]

  separator = Separator('spleeter:4stems')
  separator.separate_to_file(song_path, './', codec='mp3', bitrate="320k")
  sys.exit(0)