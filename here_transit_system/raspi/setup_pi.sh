#!/bin/bash
echo "=== Corrected Pi Transit Setup ==="

# 1. Foundations
sudo apt-get update
sudo apt-get install -y git python3-pip python3-pil libopenjp2-7 libtiff5-dev \
                        libjpeg-dev libfreetype-dev libcap-dev

# 2. Hardware and Requests
sudo raspi-config nonint do_spi 0
sudo pip3 install requests --break-system-packages

# 3. Waveshare Driver - Corrected Command
echo "Installing Waveshare Drivers..."
if [ ! -d "e-Paper" ]; then
    git clone https://github.com/waveshare/e-Paper.git
fi
cd e-Paper/RaspberryPi_JetsonNano/python
# FIXED: Using pip instead of setup.py for system-wide install
sudo pip3 install . --break-system-packages
cd ~/eink

# 4. Service Configuration (Points to eink.py)
cat <<EOF | sudo tee /etc/systemd/system/transit_display.service
[Unit]
Description=E-Ink Transit Display Client
After=graphical.target network-online.target ssh.service
Wants=graphical.target network-online.target

[Service]
ExecStartPre=/bin/sleep 15
ExecStart=/usr/bin/python3 /home/eink1/eink/eink.py
WorkingDirectory=/home/eink1/eink
Nice=10
Restart=always
RestartSec=20
User=eink1

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable transit_display.service

echo "=== Setup Complete! ==="