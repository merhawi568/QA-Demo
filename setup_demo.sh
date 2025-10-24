#!/bin/bash

# QA Agent Demo Setup Script
# Run this before your leadership presentation

echo "🚀 Setting up QA Agent Demo for Leadership"
echo "=========================================="

# Activate virtual environment
echo "📦 Activating Python environment..."
source venv/bin/activate

# Create outputs directory
echo "📁 Creating output directory..."
mkdir -p outputs

# Clear previous outputs for clean demo
echo "🧹 Clearing previous outputs..."
rm -f outputs/RUN_*.json
rm -f outputs/LEADERSHIP_DEMO_*.json

# Run a quick test to ensure everything works
echo "✅ Testing system..."
python3 -c "
from engines.workflow_engine import WorkflowEngine
from utils.data_loader import load_ticket
engine = WorkflowEngine()
ticket = load_ticket('TKT67890')
result = engine.run(ticket, scenario='happy')
print('✅ System ready!')
"

# Show demo options
echo ""
echo "🎬 Demo Options Available:"
echo "=========================="
echo "1. python3 leadership_demo.py          # Interactive leadership demo"
echo "2. python3 run_demo.py --ticket TKT67890 --scenario happy  # Happy path"
echo "3. python3 run_demo.py --ticket TKT67890 --scenario fail   # Failure detection"
echo "4. python3 main.py --scenario pass     # Simple CLI demo"
echo "5. python3 main.py --scenario fail     # Simple CLI fail demo"
echo ""
echo "📋 Demo Script: cat demo_script.md"
echo "📊 Business Metrics: python3 leadership_demo.py"
echo ""
echo "🎯 Ready for your leadership presentation!"
echo "   Run: python3 leadership_demo.py"
