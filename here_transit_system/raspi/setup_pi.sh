#!/bin/bash

echo "=== Starting Dedicated Pi Transit Setup ==="

# 1. Install System Dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-pil libopenjp2-7 libtiff5-dev \
                        libjpeg-dev libfreetype-dev libcap-dev git

# 2. Hardware and Global Python Setup
sudo raspi-config nonint do_spi 0
sudo pip3 install requests Pillow --break-system-packages

# 3. Create the strictly-after-boot Service
# We use 'graphical.target' and 'ExecStartPre' to ensure a full boot
cat <<EOF | sudo tee /etc/systemd/system/transit_display.service
[Unit]
Description=E-Ink Transit Display Client
After=graphical.target network-online.target ssh.service
Wants=graphical.target network-online.target

[Service]
# Wait an extra 10 seconds AFTER boot triggers to ensure OS stability
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 $(pwd)/eink.py
WorkingDirectory=$(pwd)

# Keep it low priority so SSH is always fast and responsive
Nice=10
Restart=always
RestartSec=20
User=$USER

[Install]
# This ensures it is part of the final boot stage
WantedBy=graphical.target
EOF

# 4. Finalize
sudo systemctl daemon-reload
sudo systemctl enable transit_display.service
echo "=== Setup Complete! Reboot to test the 'Strict Start' sequence. ==="