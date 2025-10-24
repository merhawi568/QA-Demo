#!/bin/bash

# Web Demo Startup Script
echo "🚀 Starting QA Agent Web Demo"
echo "=============================="

# Activate virtual environment
echo "📦 Activating Python environment..."
source venv/bin/activate

# Install Flask if not already installed
echo "📦 Installing Flask..."
pip install flask

# Start the web demo
echo "🌐 Starting web server..."
echo "📱 Open your browser to: http://localhost:5001"
echo "🎯 Perfect for leadership presentations!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 web_demo.py
