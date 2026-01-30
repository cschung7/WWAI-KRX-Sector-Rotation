#!/bin/bash
# KRX Chat CLI Installation Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_SCRIPT="$SCRIPT_DIR/krx_chat.py"

echo "=== KRX Chat CLI Installation ==="
echo

# Install dependencies
echo "Installing dependencies..."
pip install -q httpx rich
echo "✓ Dependencies installed"

# Make script executable
chmod +x "$CLI_SCRIPT"
echo "✓ Made script executable"

# Create symlink in /usr/local/bin (optional, requires sudo)
if [ "$1" == "--global" ]; then
    sudo ln -sf "$CLI_SCRIPT" /usr/local/bin/krx-chat
    echo "✓ Created global command: krx-chat"
fi

# Create alias suggestion
echo
echo "=== Quick Setup ==="
echo
echo "Add this alias to your ~/.bashrc or ~/.zshrc:"
echo
echo "  alias krx-chat='python $CLI_SCRIPT'"
echo
echo "With external server (recommended):"
echo "  alias krx-chat='KRX_API_BASE=http://163.239.155.97:8000 python $CLI_SCRIPT'"
echo
echo "Or with localhost:"
echo "  alias krx-chat='python $CLI_SCRIPT'"
echo
echo "=== Usage Examples ==="
echo
echo "  krx-chat                        # Interactive mode"
echo "  krx-chat \"모멘텀 종목 추천해줘\"   # Single question"
echo "  krx-chat --new \"새 대화\"        # New conversation"
echo "  krx-chat --history              # Show history"
echo
echo "Installation complete!"
