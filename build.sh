#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --windowed \
  --name Flowstate \
  --collect-all customtkinter \
  --collect-all darkdetect \
  flowstate.py

echo
 echo "Build complete: dist/Flowstate/Flowstate"
echo "Install flowstate-hosts.py separately as /usr/local/sbin/flowstate-hosts."
