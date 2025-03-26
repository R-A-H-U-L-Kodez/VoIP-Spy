import os
import json
import subprocess
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Default directories
BASE_DIR = "/home/sanjay/Downloads/voip-spy/voip-spy"
CAPTURE_DIR = BASE_DIR  # Ensuring PCAP saves in the right location
AUDIO_DIR = os.path.join(BASE_DIR, "extracted_audio")
DATA_DIR = os.path.join(BASE_DIR, "data")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "transcript")

# Ensure directories exist
for directory in [CAPTURE_DIR, AUDIO_DIR, DATA_DIR, TRANSCRIPT_DIR]:
    os.makedirs(directory, exist_ok=True)

tshark_process = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_capture', methods=['POST'])
def start_capture():
    """ Start Tshark packet capture """
    global tshark_process
    data = request.get_json()
    capture_path = data.get("capture_path", "").strip()
    
    if not capture_path:
        capture_path = os.path.join(CAPTURE_DIR, "voip_capture.pcap")

    if tshark_process and tshark_process.poll() is None:
        tshark_process.terminate()
    
    try:
        if not os.access(CAPTURE_DIR, os.W_OK):
            return jsonify({"message": "❌ Capture directory is not writable. Check permissions!"}), 500

        tshark_process = subprocess.Popen(
            ["tshark", "-i", "wlo1", "-w", capture_path, "-F", "pcap"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return jsonify({"message": f"✅ Capture started at {capture_path}"})
    except Exception as e:
        return jsonify({"message": f"❌ Error starting capture: {e}"}), 500

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    """ Stop Tshark capture """
    global tshark_process
    try:
        if tshark_process and tshark_process.poll() is None:
            tshark_process.terminate()
            tshark_process.wait()
        return jsonify({"message": "✅ Capture stopped and saved."})
    except Exception as e:
        return jsonify({"message": f"❌ Error stopping capture: {e}"}), 500
        
        
@app.route('/download_pcap')
def download_pcap():
    """
    Serve the PCAP file for download.
    """
    if os.path.exists(capture_path):
        return send_file(capture_path, as_attachment=True)
    else:
        return jsonify({"message": "File not found at the specified path."}), 404


@app.route('/listen_audio', methods=['POST'])
def listen_audio():
    """
    Allow the user to select a .pcap file and process it to extract and play audio.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"message": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "No file selected"}), 400

        # Save the uploaded file temporarily
        temp_pcap_path = "/tmp/uploaded_capture.pcap"
        file.save(temp_pcap_path)

        # Extract audio from the uploaded .pcap file
        subprocess.Popen(["python3", "scripts/voip6.py", temp_pcap_path])

        return jsonify({"message": "Audio extraction started"})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500



@app.route('/get_rtp_metadata', methods=['POST'])
def get_rtp_metadata():
    """ Process PCAP file and extract RTP metadata """
    if 'file' not in request.files:
        return jsonify({"message": "❌ No file provided."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "❌ No file selected."}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata_filename = f"rtp_metadata_{timestamp}.json"
    metadata_path = os.path.join(DATA_DIR, metadata_filename)

    try:
        # Simulated RTP extraction (Replace this with actual logic)
        rtp_metadata = [
            {"source_ip": "192.168.1.10", "destination_ip": "192.168.1.20", "source_port": 4000, "destination_port": 5000, "ssrc": 12345, "payload_type": 8, "packets": 200, "duration": "30s"}
        ]

        with open(metadata_path, "w") as f:
            json.dump({"rtp_data": rtp_metadata}, f, indent=4)

        return jsonify({"message": "✅ RTP metadata extracted", "metadata_path": metadata_path, "rtp_data": rtp_metadata})
    except Exception as e:
        return jsonify({"message": f"❌ Error processing RTP metadata: {e}"}), 500

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    """ Convert speech from WAV file to text and save output """
    if 'file' not in request.files:
        return jsonify({"message": "❌ No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "❌ No file selected"}), 400

    if not file.filename.lower().endswith(".wav"):
        return jsonify({"message": "❌ Only WAV files are supported"}), 400
    
    temp_audio_path = os.path.join("/tmp", file.filename)
    file.save(temp_audio_path)

    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        output_filename = f"output-{timestamp}.txt"
        output_path = os.path.join(TRANSCRIPT_DIR, output_filename)

        with open(output_path, "w") as f:
            f.write(text)

        return jsonify({"message": "✅ Speech recognized successfully", "transcript_path": output_path, "text": text})
    except sr.UnknownValueError:
        return jsonify({"message": "⚠️ Speech could not be understood."}), 400
    except sr.RequestError:
        return jsonify({"message": "❌ Could not request results from the recognition service."}), 500

if __name__ == '__main__':
    app.run(debug=True)

