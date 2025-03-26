import os
import hashlib
from pydub import AudioSegment
from collections import defaultdict
from scapy.all import *
from datetime import datetime
import argparse

# Ensure ffmpeg is available
os.environ["FFMPEG_BINARY"] = "ffmpeg"

# Setup command-line argument parsing
parser = argparse.ArgumentParser(description="Process RTP from a .pcap file and extract audio.")
parser.add_argument('file_path', type=str, help="Path to the .pcap file")
args = parser.parse_args()

# Load the .pcap file
file_path = args.file_path  # Get the file path from the command-line argument
packets = rdpcap(file_path)

# Generate a unique directory name based on the current date and time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = os.path.join("extracted_audio", timestamp)

# Create the output directory
os.makedirs(output_dir, exist_ok=True)

# Define voice payload types (G.711 u-law, A-law, and dynamic types)
VOICE_PAYLOAD_TYPES = {0, 8}  # Add more types as needed (e.g., 96-127 for dynamic)

# Identify all RTP streams
rtp_streams = defaultdict(lambda: {
    'source_ip': None,
    'destination_ip': None,
    'source_port': None,
    'destination_port': None,
    'ssrc': None,
    'payload_type': None,
    'packets': {},  # Store packets by sequence number
    'timestamps': []  # Store timestamps to calculate duration
})

# Extract RTP payloads grouped by unique stream identifier
for packet in packets:
    try:
        if UDP in packet:
            rtp_data = bytes(packet[UDP].payload)
            if len(rtp_data) >= 12:  # RTP header is at least 12 bytes
                # Extract RTP header fields
                version = (rtp_data[0] >> 6) & 0x03  # RTP version (should be 2)
                padding = (rtp_data[0] >> 5) & 0x01  # Padding bit
                extension = (rtp_data[0] >> 4) & 0x01  # Extension bit
                csrc_count = rtp_data[0] & 0x0F  # CSRC count
                payload_type = rtp_data[1] & 0x7F  # Payload type
                sequence_number = int.from_bytes(rtp_data[2:4], byteorder='big')  # Sequence number
                timestamp = int.from_bytes(rtp_data[4:8], byteorder='big')  # Timestamp
                ssrc = int.from_bytes(rtp_data[8:12], byteorder='big')  # SSRC

                # If it's not a voice stream (based on payload type), skip it
                if payload_type not in VOICE_PAYLOAD_TYPES:
                    continue

                # Calculate RTP header length (12 bytes + CSRCs + extension)
                header_length = 12 + (csrc_count * 4)
                if extension:
                    extension_length = int.from_bytes(rtp_data[header_length + 2:header_length + 4], byteorder='big')
                    header_length += 4 + (extension_length * 4)

                # Extract payload
                payload = rtp_data[header_length:]

                # Unique stream identifier
                stream_id = (packet[IP].src, packet[UDP].sport, packet[IP].dst, packet[UDP].dport, ssrc)

                # Store stream details
                if not rtp_streams[stream_id]['source_ip']:
                    rtp_streams[stream_id]['source_ip'] = packet[IP].src
                    rtp_streams[stream_id]['destination_ip'] = packet[IP].dst
                    rtp_streams[stream_id]['source_port'] = packet[UDP].sport
                    rtp_streams[stream_id]['destination_port'] = packet[UDP].dport
                    rtp_streams[stream_id]['ssrc'] = ssrc
                    rtp_streams[stream_id]['payload_type'] = payload_type

                # Store RTP packet by sequence number
                rtp_streams[stream_id]['packets'][sequence_number] = payload
                rtp_streams[stream_id]['timestamps'].append(timestamp)

    except Exception as e:
        print(f"Error parsing packet: {e}")
        continue

# Remove duplicate audio streams based on SSRC
unique_streams = {}
for stream_id, details in rtp_streams.items():
    ssrc = details['ssrc']
    if ssrc not in unique_streams:
        unique_streams[ssrc] = details  # Only add the first stream with a unique SSRC
    else:
        print(f"Duplicate stream found with SSRC {ssrc}. Skipping duplicate.")

# Process each unique RTP stream separately
audio_files = []
for ssrc, details in unique_streams.items():
    if details['packets']:
        # Ensure at least one packet before processing
        if len(details['packets']) > 1:
            # Calculate the duration based on the timestamps
            timestamps = sorted(details['timestamps'])
            duration = (timestamps[-1] - timestamps[0]) / 8000.0  # Assuming 8000 Hz sample rate

            if duration < 2.0:  # Skip streams with less than 2 seconds of audio
                print(f"Skipping SSRC {ssrc} due to short duration ({duration:.2f} seconds).")
                continue

            # Sort packets by sequence number
            sorted_payloads = [details['packets'][seq] for seq in sorted(details['packets'].keys())]
            raw_audio = b''.join(sorted_payloads)

            if not raw_audio:  # Skip if there's no audio
                print(f"Skipping SSRC {ssrc} as it has no audio.")
                continue

            # Save raw audio file
            raw_file = os.path.join(output_dir, f"rtp_stream_{ssrc}.raw")
            with open(raw_file, 'wb') as f:
                f.write(raw_audio)

            # Convert raw audio to WAV using ffmpeg
            wav_file = os.path.join(output_dir, f"rtp_stream_{ssrc}.wav")
            ffmpeg_command = f"ffmpeg -f mulaw -ar 8000 -ac 1 -i {raw_file} {wav_file}"
            os.system(ffmpeg_command)

            audio_files.append(wav_file)
            print(f"Extracted audio saved to: {wav_file}")

            # Print details
            print(f"\nExtracted RTP Stream (SSRC: {ssrc}):")
            print(f"  Source IP: {details['source_ip']}")
            print(f"  Destination IP: {details['destination_ip']}")
            print(f"  Source Port: {details['source_port']}")
            print(f"  Destination Port: {details['destination_port']}")
            print(f"  Payload Type: {details['payload_type']}")
            print(f"  Packets: {len(details['packets'])}")
            print(f"  Duration: {duration:.2f} seconds")
        else:
            print(f"Skipping SSRC {ssrc} due to insufficient packets.")

# Now automatically merge the audio files in the output directory

# Function to calculate hash of an audio file
def get_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Automatically identify .wav files in the directory
audio_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".wav")]

# Debug: Print out the list of audio files to merge
print(f"Audio files to merge: {audio_files}")

# Dictionary to keep track of already processed audio files (using hashes)
seen_hashes = {}
final_audio_files = []

# Merge both audio streams into one (if there are exactly two files)
for audio_file in audio_files:
    file_hash = get_file_hash(audio_file)
    
    if file_hash not in seen_hashes:
        seen_hashes[file_hash] = audio_file
        final_audio_files.append(audio_file)
    else:
        print(f"Duplicate audio file detected: {audio_file}. Skipping.")

# Now, let's merge the remaining unique audio files (if there are exactly two files)
if len(final_audio_files) >= 2:
    # Load the audio files with pydub
    caller1_audio = AudioSegment.from_file(final_audio_files[0])
    caller2_audio = AudioSegment.from_file(final_audio_files[1])

    # Ensure both audios have the same sample rate (if not, resample)
    if caller1_audio.frame_rate != caller2_audio.frame_rate:
        caller2_audio = caller2_audio.set_frame_rate(caller1_audio.frame_rate)

    # Set the same duration for both (if they are of different lengths, this step helps)
    min_length = min(len(caller1_audio), len(caller2_audio))

    # Truncate the longer audio or pad the shorter one with silence to match the minimum length
    caller1_audio = caller1_audio[:min_length]
    caller2_audio = caller2_audio[:min_length]

    # Combine the audio files (this will mix them in a stereo format: left = caller1, right = caller2)
    combined_audio = AudioSegment.from_mono_audiosegments(caller1_audio, caller2_audio)

    # Export the combined audio to a new file
    merged_wav = os.path.join(output_dir, "merged_audio.wav")
    combined_audio.export(merged_wav, format="wav")

    # Print the merged file path for Flask to capture
    print(merged_wav)
else:
    print("Insufficient unique audio streams to merge.")

