#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Building Frontend client..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete!"
