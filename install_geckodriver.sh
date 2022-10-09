#!/bin/bash

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Update, upgrade and install wget and Firefox
apt-get update
apt-get -y upgrade
apt-get -y install --no-install-recommends wget firefox-esr
apt-get clean
rm -rf /var/lib/apt/lists/*

# Get geckodriver binary release from the repo
wget https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz
tar -xvzf geckodriver*
chmod +x geckodriver
mkdir bin
mv geckodriver bin