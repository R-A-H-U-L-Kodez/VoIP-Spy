import subprocess
import os
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

# Default directory for capture file
DEFAULT_CAPTURE_DIR = "/home/sanjay/Downloads/voip-spy/"
DEFAULT_FILE_NAME = "voip_capture.pcap"
AUDIO_DIR = 'extracted_audio' 

# Global variable for the capture file path (this will be updated dynamically based on user input)
capture_path = os.path.join(DEFAULT_CAPTURE_DIR, DEFAULT_FILE_NAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_capture', methods=['POST'])
def start_capture():
    """
    Start capturing packets using Tshark with the user-defined or default capture file path.
    """
    global capture_path

    # Get the user-provided capture path (if any)
    data = request.get_json()
    user_capture_path = data.get("capture_path", "").strip()

    if user_capture_path:
        # If user provides a path, use it
        capture_path = os.path.abspath(user_capture_path)
    else:
        # If no path is provided, use the default path
        capture_path = os.path.join(DEFAULT_CAPTURE_DIR, DEFAULT_FILE_NAME)

    try:
        subprocess.Popen(["tshark", "-i", "wlo1", "-w", capture_path])  # Adjust interface (wlo1) accordingly
        return jsonify({"message": f"Capture started and will be saved to {capture_path}"})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    """
    Stop capturing packets and provide a downloadable PCAP file.
    """
    try:
        os.system("pkill tshark")  # Stop Tshark process

        # Ensure the file exists before providing download
        if os.path.exists(capture_path):
            return jsonify({"message": "Capture stopped", "file_url": "/download_pcap"})
        else:
            return jsonify({"message": "No capture file found at the specified path."}), 500
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500

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

    

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Route to serve audio files."""
    if os.path.exists(os.path.join(AUDIO_DIR, filename)):
        return send_from_directory(AUDIO_DIR, filename)
    else:
        return "File not found", 404


@app.route('/load_capture', methods=['POST'])
def load_capture():
    """
    Load a capture file from a user-specified location
    """
    try:
        file = request.files['file']
        file.save(PCAP_FILE)
        return jsonify({"message": "Capture loaded"})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500

@app.route('/get_voip_data')
def get_voip_data():
    """
    Read RTP packets from the captured file and return packet info.
    """
    voip_data = []

    try:
        command = ["tshark", "-r", PCAP_FILE, "-T", "fields", "-e", "ip.src", "-e", "ip.dst", "-e", "frame.time", "-e", "udp.srcport", "-e", "udp.dstport"]
        output = subprocess.check_output(command).decode("utf-8")

        for line in output.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 5:
                voip_data.append({
                    "source_ip": parts[0],
                    "dest_ip": parts[1],
                    "timestamp": parts[2],
                    "protocol": "RTP",
                    "src_port": parts[3],
                    "dest_port": parts[4]
                })
    except Exception as e:
        print(f"Error reading VoIP data: {e}")

    return jsonify(voip_data)

if __name__ == '__main__':
    app.run(debug=True)

