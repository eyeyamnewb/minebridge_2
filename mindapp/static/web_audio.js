// web_audio.js
// Utility for live audio recording with voice activity detection (VAD)

let mediaRecorder;
let audioChunks = [];
let audioContext, analyser, microphone, javascriptNode;
let speaking = false;
let silenceTimeout;

function startVoiceDetection() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            microphone = audioContext.createMediaStreamSource(stream);
            javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

            analyser.smoothingTimeConstant = 0.8;
            analyser.fftSize = 1024;

            microphone.connect(analyser);
            analyser.connect(javascriptNode);
            javascriptNode.connect(audioContext.destination);

            javascriptNode.onaudioprocess = function() {
                let array = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(array);
                let values = 0;

                for (let i = 0; i < array.length; i++) {
                    values += array[i];
                }
                let average = values / array.length;

                if (average > 10) { // Threshold for speech detection
                    if (!speaking) {
                        speaking = true;
                        startRecording(stream);
                        clearTimeout(silenceTimeout);
                    }
                } else {
                    if (speaking) {
                        clearTimeout(silenceTimeout);
                        silenceTimeout = setTimeout(() => {
                            speaking = false;
                            stopRecording();
                        }, 1000); // Stop after 1s of silence
                    }
                }
            };
        })
        .catch(err => {
            alert('Microphone access denied or not available.');
        });
}

function startRecording(stream) {
    if (mediaRecorder && mediaRecorder.state === "recording") return;
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
        if (audioChunks.length > 0) {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            sendAudioToBackend(audioBlob);
            audioChunks = [];
        }
    };
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }
}

function sendAudioToBackend(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    fetch('/your-backend-endpoint/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Server response:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// To use: call startVoiceDetection() to begin live voice activity detection and recording.
