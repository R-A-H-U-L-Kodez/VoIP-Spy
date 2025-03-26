import os
from collections import defaultdict
from scapy.all import *
from datetime import datetime
import json

# Ensure ffmpeg is available
os.environ["FFMPEG_BINARY"] = "ffmpeg"

# Set base directory for storing metadata
BASE_DIR = "/home/sanjay/Downloads/voip-spy/voip-spy/data"

def extract_rtp_streams(pcap_file):
    packets = rdpcap(pcap_file)

    # Generate a timestamped directory for this session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(BASE_DIR, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # Define metadata file path
    metadata_file = os.path.join(output_dir, "metadata.json")

    # Define supported voice payload types
    VOICE_PAYLOAD_TYPES = {0, 8}

    # RTP stream dictionary
    rtp_streams = defaultdict(lambda: {
        'source_ip': None,
        'destination_ip': None,
        'source_port': None,
        'destination_port': None,
        'ssrc': None,
        'payload_type': None,
        'packets': {},
        'timestamps': []
    })

    # Process packets
    for packet in packets:
        try:
            if UDP in packet:
                rtp_data = bytes(packet[UDP].payload)
                if len(rtp_data) >= 12:
                    payload_type = rtp_data[1] & 0x7F
                    sequence_number = int.from_bytes(rtp_data[2:4], byteorder='big')
                    timestamp = int.from_bytes(rtp_data[4:8], byteorder='big')
                    ssrc = int.from_bytes(rtp_data[8:12], byteorder='big')

                    if payload_type not in VOICE_PAYLOAD_TYPES:
                        continue

                    payload = rtp_data[12:]
                    stream_id = (packet[IP].src, packet[UDP].sport, packet[IP].dst, packet[UDP].dport, ssrc)

                    if not rtp_streams[stream_id]['source_ip']:
                        rtp_streams[stream_id]['source_ip'] = packet[IP].src
                        rtp_streams[stream_id]['destination_ip'] = packet[IP].dst
                        rtp_streams[stream_id]['source_port'] = packet[UDP].sport
                        rtp_streams[stream_id]['destination_port'] = packet[UDP].dport
                        rtp_streams[stream_id]['ssrc'] = ssrc
                        rtp_streams[stream_id]['payload_type'] = payload_type

                    rtp_streams[stream_id]['packets'][sequence_number] = payload
                    rtp_streams[stream_id]['timestamps'].append(timestamp)
        except Exception as e:
            print(f"⚠️ Error processing packet: {e}")
            continue

    # Save RTP metadata
    rtp_data_list = []
    for stream_id, details in rtp_streams.items():
        if details['packets']:
            timestamps = sorted(details['timestamps'])
            duration = (timestamps[-1] - timestamps[0]) / 8000.0 if timestamps else 0

            if duration < 2.0:
                continue

            rtp_data_list.append({
                "source_ip": details['source_ip'],
                "destination_ip": details['destination_ip'],
                "source_port": details['source_port'],
                "destination_port": details['destination_port'],
                "ssrc": details['ssrc'],
                "payload_type": details['payload_type'],
                "packets": len(details['packets']),
                "duration": round(duration, 2)
            })

    with open(metadata_file, "w") as meta_file:
        json.dump(rtp_data_list, meta_file, indent=4)

    print(f"✅ RTP metadata saved: {metadata_file}")  # Only essential message

    return metadata_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python extract_rtp.py <pcap_file>")
        sys.exit(1)

    pcap_file = sys.argv[1]
    if not os.path.exists(pcap_file):
        print(f"❌ File not found: {pcap_file}")
        sys.exit(1)

    extract_rtp_streams(pcap_file)

