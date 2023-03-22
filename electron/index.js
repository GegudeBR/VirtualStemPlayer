const vocals = new Audio('audio/vocals.mp3');
const other = new Audio('audio/other.mp3');
const drums = new Audio('audio/drums.mp3');
const bass = new Audio('audio/bass.mp3');
const playButton = document.querySelector('.stem-player button');

playButton.addEventListener('click', function() {
  if (playButton.classList.contains('playing')) {
    playButton.classList.remove('playing');
    playButton.style.backgroundImage = 'url("images/play.png")';
    // Add logic to pause the audio playback
    
    vocals.pause();
    other.pause();
    drums.pause();
    bass.pause();

  } else {
    playButton.classList.add('playing');
    playButton.style.backgroundImage = 'url("images/pause.png")';
    // Add logic to start the audio playback

    vocals.play();
    other.play();
    drums.play();
    bass.play();
  }
});

const vocalTimeSlider = document.querySelector('.vocal-volume-slider');
vocalTimeSlider.addEventListener('input', () => {
  // Set vocal audio volume to the value of the slider
  vocals.volume = vocalTimeSlider.value / 100;
});

const otherTimeSlider = document.querySelector('.other-volume-slider');
otherTimeSlider.addEventListener('input', () => {
  // Set other audio volume to the value of the slider
  other.volume = otherTimeSlider.value / 100;
});

const drumsTimeSlider = document.querySelector('.drums-volume-slider');
drumsTimeSlider.addEventListener('input', () => {
  // Set drums audio volume to the value of the slider
  drums.volume = drumsTimeSlider.value / 100;
});

const bassTimeSlider = document.querySelector('.bass-volume-slider');
bassTimeSlider.addEventListener('input', () => {
  // Set bass audio volume to the value of the slider
  bass.volume = bassTimeSlider.value / 100;
});

let previousVolumeVocal = 0;
let previousVolumeOther = 0;
let previousVolumeDrums = 0;
let previousVolumeBass = 0;
let isMuted = false;

document.addEventListener("keydown", function(event) {
  // Mute all stems when the "m" key is pressed
  if (event.key === "m" || event.key === "M") {
    if (!isMuted) {
      // Save the previous volume
      previousVolumeVocal = vocals.volume;
      previousVolumeOther = other.volume;
      previousVolumeDrums = drums.volume;
      previousVolumeBass = bass.volume;

      // Mute all stems
      vocals.volume = 0;
      other.volume = 0;
      drums.volume = 0;
      bass.volume = 0;
    } else {
      // Restore the previous volume
      vocals.volume = previousVolumeVocal;
      other.volume = previousVolumeOther;
      drums.volume = previousVolumeDrums;
      bass.volume = previousVolumeBass;
    }

    // Update slider values
    vocalTimeSlider.value = vocals.volume * 100;
    otherTimeSlider.value = other.volume * 100;
    drumsTimeSlider.value = drums.volume * 100;
    bassTimeSlider.value = bass.volume * 100;

    isMuted = !isMuted;
  }
});




// Get the music time slider and music time bar elements
const musicTimeSlider = document.querySelector('.music-time-slider');
const musicTimeBar = document.querySelector('.music-time-bar');

// Add an event listener to the music time slider
musicTimeSlider.addEventListener('input', () => {
  // Calculate the percentage of the music that has been played
  const playedPercentage = (musicTimeSlider.value / musicTimeSlider.max) * 100;

  // Set the width of the music time bar to the played percentage
  musicTimeBar.style.width = `${playedPercentage}%`;

  // Calculate the current timestamp of the song
  const currentTime = (musicTimeSlider.value / musicTimeSlider.max) * vocals.duration;

  // Set the current timestamp of the song
  vocals.currentTime = currentTime;
  other.currentTime = currentTime;
  drums.currentTime = currentTime;
  bass.currentTime = currentTime;
});

setInterval(() => {
  // Calculate the percentage of the music that has been played
  const playedPercentage = (vocals.currentTime / vocals.duration) * 100;
  // Set the width of the music time bar to the played percentage
  musicTimeBar.style.width = `${playedPercentage}%`;

  // Set the value of the music time slider to the current timestamp of the song
  musicTimeSlider.value = playedPercentage;
  
}, 1000);