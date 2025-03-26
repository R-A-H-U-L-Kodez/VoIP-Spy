// Get Radar Element
const radar = document.querySelector('.radar');

// Start Capture - Activate Radar Animation
document.getElementById('startCapture').addEventListener('click', () => {
    const capturePath = document.getElementById('capturePath').value.trim();
    if (!capturePath) {
        alert("❌ Please enter a path or filename.");
        return;
    }

    fetch('/start_capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ capture_path: capturePath })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        radar.classList.add('active'); // Start radar animation
    })
    .catch(error => console.error('⚠️ Capture Start Error:', error));
});

// Stop Capture - Deactivate Radar Animation
document.getElementById('stopCapture').addEventListener('click', () => {
    fetch('/stop_capture', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            radar.classList.remove('active'); // Stop radar animation
        })
        .catch(error => console.error('⚠️ Capture Stop Error:', error));
});

// Listen to Audio Functionality
document.getElementById('listenAudio').addEventListener('click', function() {
    const pcapFileInput = document.getElementById('pcapFileInput');
    const capturePath = document.getElementById('capturePath').value;

    if (!pcapFileInput.files.length) {
        alert('Please select a .pcap file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', pcapFileInput.files[0]);
    formData.append('capturePath', capturePath);

    fetch('/listen_audio', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
        }
        if (data.audio_path) {
            // Show the path where the audio was saved
            document.getElementById('audioPath').innerText = data.audio_path;
            document.getElementById('audioPathSection').style.display = 'block';
        }
    })
    .catch(error => console.error('Error:', error));
});


// Get RTP Data Functionality
document.getElementById('GetData').addEventListener('click', () => {
    let fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.pcap';

    fileInput.onchange = async (e) => {
        let file = e.target.files[0];
        if (!file) return;

        let formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/get_rtp_metadata', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.rtp_data) {
                updateRTPTable(data.rtp_data);
            } else {
                alert(data.message || "⚠️ No RTP streams found.");
            }
        } catch (error) {
            console.error('⚠️ Get RTP Data Error:', error);
        }
    };

    fileInput.click();
});

// Function to update the RTP Data Table
function updateRTPTable(rtpData) {
    let tableBody = document.getElementById('rtpTableBody');
    tableBody.innerHTML = ''; // Clear existing data

    rtpData.forEach(entry => {
        let row = document.createElement('tr');
        row.innerHTML = `
            <td>${entry.source_ip}</td>
            <td>${entry.destination_ip}</td>
            <td>${entry.source_port}</td>
            <td>${entry.destination_port}</td>
            <td>${entry.ssrc}</td>
            <td>${entry.payload_type}</td>
            <td>${entry.packets}</td>
            <td>${entry.duration}</td>
        `;
        tableBody.appendChild(row);
    });

    alert("✅ RTP Data Loaded Successfully!");
}

// Function to fetch the latest RTP metadata dynamically every 5 seconds
async function loadRTPMetadata() {
    try {
        const response = await fetch('/latest_metadata');
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const data = await response.json();
        if (!data.voip_data || data.voip_data.length === 0) {
            console.log("No RTP streams found.");
            return;
        }

        updateRTPTable(data.voip_data);
        console.log("✅ RTP Metadata updated successfully.");
    } catch (error) {
        console.error('⚠️ Error loading RTP metadata:', error);
    }
}

// Auto-refresh RTP metadata every 5 seconds
setInterval(loadRTPMetadata, 5000);
loadRTPMetadata(); // Load once on page load

// Speech to Text Functionality
document.getElementById("speechToText").addEventListener("click", function () {
    let fileInput = document.getElementById("wavFileInput");
    let file = fileInput.files[0];

    if (!file) {
        alert("❌ Please select a WAV file.");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    fetch("/speech_to_text", { method: "POST", body: formData })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Speech recognized successfully") {
            alert("✅ Transcription saved: " + data.transcript_path);
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error("⚠️ Speech-to-Text Error:", error));
});

