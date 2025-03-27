# VoIP-Spy

VoIP-Spy is a VoIP monitoring tool using TShark to capture and analyze SIP and RTP packets for call logging, security auditing, and intrusion detection. It enhances VoIP security by detecting anomalies and optimizing call performance. Built with expertise in VoIP protocols, packet analysis, and network security.

## 📌 Features

### 📞 VoIP Monitoring
- **Packet Capture**: Uses TShark to capture SIP and RTP packets.
- **Call Logging**: Logs call details and durations.
- **Security Auditing**: Analyzes packets for security vulnerabilities.
- **Intrusion Detection**: Detects anomalies and potential intrusions.

### 🔒 Security
- **Anomaly Detection**: Identifies unusual patterns in VoIP traffic.
- **Performance Optimization**: Monitors and enhances call performance.

## ⚙️ Tech Stack
- **Python**: Core programming language.
- **TShark**: For packet capturing and analysis.
- **JavaScript**: For front-end functionalities.
- **CSS & HTML**: For styling and structure.

## 📁 Folder Structure

```
VoIP-Spy/
│── src/                     # Source code
│   ├── capture/             # Packet capturing scripts
│   ├── analysis/            # Packet analysis scripts
│   ├── logging/             # Call logging scripts
│   ├── security/            # Security auditing scripts
│   ├── utils/               # Utility functions
│   ├── main.py              # Main entry point
│
│── web/                     # Web interface
│   ├── static/              # Static assets (CSS, JS)
│   ├── templates/           # HTML templates
│   ├── app.js               # Web server entry point
│
│── README.md                # Project documentation
│── requirements.txt         # Python dependencies
│── .gitignore               # Files to ignore in Git
│
```

## 🚀 How to Run Locally

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/R-A-H-U-L-Kodez/VoIP-Spy.git
cd VoIP-Spy
```

### 2️⃣ Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run the Application
```bash
python src/main.py
```

### 5️⃣ Access the Web Interface
Open your browser and navigate to `http://localhost:5000`

## 📜 License
This project is open-source under the MIT License.

## 🤝 Contributions & Feedback
Want to contribute? Feel free to fork the repo and submit a pull request! If you find any issues, open an issue or reach out. 🚀
