import sys
import os
import soundfile as sf
import demucs

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

    with sf.SoundFile(song_path) as f:
        sample_rate = f.samplerate
        channels = f.channels
        duration = f.duration

        # Read the audio data
        audio_bytes = f.read(channels * int(duration * sample_rate))

    # Create the Demucs model with default settings
    model = demucs.models.Demucs(download=False)

    # Perform source separation on the input audio
    sources = model.separate(audio_bytes, split=True)

    # Save the separated sources to individual MP3 files with a bitrate of 320 kbps
    for i, source in enumerate(sources):
        output_file = f"source_{i}.mp3"
        sf.write(output_file, source, sample_rate, format="mp3", bitrate="320k")

    sys.exit(0)