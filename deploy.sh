#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== Pulling latest code ==="
git pull

echo "=== Building frontend ==="
cd frontend
npm install --silent
npm run build
cd ..

echo "=== Restarting backend ==="
sudo systemctl restart lab-manager
sleep 4

echo "=== Running regression tests ==="
cd backend
python -m pytest tests/test_kvm_regression.py -v
cd ..

echo ""
echo "=== Deploy complete ==="
git log -1 --oneline
