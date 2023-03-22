const audio = new Audio('audio/track.mp3');
const playButton = document.querySelector('.stem-player button');

playButton.addEventListener('click', function() {
  if (playButton.classList.contains('playing')) {
    playButton.classList.remove('playing');
    playButton.style.backgroundImage = 'url("images/play.png")';
    // Add logic to pause the audio playback
    audio.pause();
  } else {
    playButton.classList.add('playing');
    playButton.style.backgroundImage = 'url("images/pause.png")';
    // Add logic to start the audio playback
    audio.play();
  }
});
