#!/bin/bash
#
# Installation script for Quizzer IRC Bot
#
# This script installs all required dependencies for the bot.
# It REQUIRES a virtual environment and will create one automatically.
# Supports Debian/Ubuntu, RedHat/CentOS, and generic Python installations.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and bot root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIRECTORY="$SCRIPT_DIR"
VENV_PATH="$BOT_DIRECTORY/.venv"

# Detect OS
detect_os() {
    # Check for BSD systems first (they may not have /etc/os-release)
    if [ -f /usr/bin/uname ]; then
        UNAME_S=$(uname -s)
        if [ "$UNAME_S" = "FreeBSD" ]; then
            OS="freebsd"
            return 0
        elif [ "$UNAME_S" = "OpenBSD" ]; then
            OS="openbsd"
            return 0
        elif [ "$UNAME_S" = "NetBSD" ]; then
            OS="netbsd"
            return 0
        fi
    fi
    
    # Check for Linux distributions
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        
        # Handle special cases
        if [ "$OS" = "arch" ] || [ "$OS" = "archlinux" ]; then
            OS="arch"
        elif [ "$OS" = "alpine" ]; then
            OS="alpine"
        elif [ "$OS" = "opensuse-leap" ] || [ "$OS" = "opensuse-tumbleweed" ] || [ "$OS" = "sles" ]; then
            OS="suse"
        fi
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
    elif [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/arch-release ]; then
        OS="arch"
    elif [ -f /etc/alpine-release ]; then
        OS="alpine"
    else
        OS="unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running as root (for sudo checks)
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        echo -e "${YELLOW}Note: Some operations may require sudo privileges${NC}"
        echo "You may be prompted for your password"
    fi
}

# Install system packages
install_system_packages() {
    echo -e "${YELLOW}Checking system packages...${NC}"
    
    MISSING_PACKAGES=()
    
    # Check Python 3
    if ! command_exists python3; then
        MISSING_PACKAGES+=("python3")
    fi
    
    # Check python3-venv or equivalent (OS-specific)
    if [ "$OS" = "debian" ] || [ "$OS" = "ubuntu" ]; then
        if ! dpkg -l | grep -q "^ii.*python3-venv"; then
            MISSING_PACKAGES+=("python3-venv")
        fi
    elif [ "$OS" = "rhel" ] || [ "$OS" = "centos" ] || [ "$OS" = "fedora" ]; then
        # On RHEL/CentOS/Fedora, venv is usually in python3 package
        # But we check if python3 -m venv works
        if ! python3 -m venv --help >/dev/null 2>&1; then
            MISSING_PACKAGES+=("python3-devel")
        fi
    elif [ "$OS" = "alpine" ]; then
        if ! apk info -e py3-venv >/dev/null 2>&1; then
            MISSING_PACKAGES+=("py3-venv")
        fi
    elif [ "$OS" = "arch" ]; then
        # Arch includes venv in python package, just check if it works
        if ! python3 -m venv --help >/dev/null 2>&1; then
            MISSING_PACKAGES+=("python")
        fi
    elif [ "$OS" = "suse" ]; then
        # SUSE includes venv in python3 package
        if ! python3 -m venv --help >/dev/null 2>&1; then
            MISSING_PACKAGES+=("python3")
        fi
    elif [ "$OS" = "freebsd" ] || [ "$OS" = "openbsd" ] || [ "$OS" = "netbsd" ]; then
        # BSD systems include venv in python3 package
        if ! python3 -m venv --help >/dev/null 2>&1; then
            MISSING_PACKAGES+=("python3")
        fi
    else
        # Generic check for other systems
        if ! python3 -m venv --help >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠ Could not verify venv module. Continuing anyway...${NC}"
        fi
    fi
    
    # Check pip (OS-specific package names)
    if ! command_exists pip3; then
        if [ "$OS" = "alpine" ]; then
            MISSING_PACKAGES+=("py3-pip")
        elif [ "$OS" = "arch" ]; then
            MISSING_PACKAGES+=("python-pip")
        elif [ "$OS" = "freebsd" ]; then
            # FreeBSD uses versioned packages like py38-pip
            PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2 | tr -d '.')
            MISSING_PACKAGES+=("py${PYTHON_VERSION}-pip")
        elif [ "$OS" = "openbsd" ]; then
            MISSING_PACKAGES+=("py3-pip")
        elif [ "$OS" = "netbsd" ]; then
            # NetBSD uses versioned packages
            PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2 | tr -d '.')
            MISSING_PACKAGES+=("py${PYTHON_VERSION}-pip")
        else
            MISSING_PACKAGES+=("python3-pip")
        fi
    fi
    
    if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All required system packages are installed${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Missing system packages: ${MISSING_PACKAGES[*]}${NC}"
    echo "Installing missing packages..."
    
    case $OS in
        debian|ubuntu)
            echo "Updating package list..."
            sudo apt-get update
            echo "Installing: ${MISSING_PACKAGES[*]}"
            sudo apt-get install -y "${MISSING_PACKAGES[@]}"
            ;;
        rhel|centos|fedora)
            if command_exists dnf; then
                echo "Installing: ${MISSING_PACKAGES[*]}"
                sudo dnf install -y "${MISSING_PACKAGES[@]}"
            elif command_exists yum; then
                echo "Installing: ${MISSING_PACKAGES[*]}"
                sudo yum install -y "${MISSING_PACKAGES[@]}"
            else
                echo -e "${RED}✗ Could not install packages (dnf/yum not found)${NC}"
                return 1
            fi
            ;;
        arch)
            echo "Updating package database..."
            sudo pacman -Sy
            echo "Installing: ${MISSING_PACKAGES[*]}"
            sudo pacman -S --noconfirm "${MISSING_PACKAGES[@]}"
            ;;
        alpine)
            echo "Updating package index..."
            sudo apk update
            echo "Installing: ${MISSING_PACKAGES[*]}"
            sudo apk add "${MISSING_PACKAGES[@]}"
            ;;
        suse)
            echo "Installing: ${MISSING_PACKAGES[*]}"
            sudo zypper install -y "${MISSING_PACKAGES[@]}"
            ;;
        freebsd)
            echo "Updating package database..."
            sudo pkg update
            echo "Installing: ${MISSING_PACKAGES[*]}"
            sudo pkg install -y "${MISSING_PACKAGES[@]}"
            ;;
        openbsd)
            echo "Installing: ${MISSING_PACKAGES[*]}"
            # OpenBSD uses doas or sudo, try both
            if command_exists doas; then
                doas pkg_add "${MISSING_PACKAGES[@]}"
            else
                sudo pkg_add "${MISSING_PACKAGES[@]}"
            fi
            ;;
        netbsd)
            echo "Updating package database..."
            sudo pkgin update
            echo "Installing: ${MISSING_PACKAGES[*]}"
            sudo pkgin install -y "${MISSING_PACKAGES[@]}"
            ;;
        *)
            echo -e "${YELLOW}⚠ Unknown OS. Please install manually: ${MISSING_PACKAGES[*]}${NC}"
            echo ""
            echo "Common package managers:"
            echo "  Debian/Ubuntu: sudo apt-get install ${MISSING_PACKAGES[*]}"
            echo "  RHEL/CentOS/Fedora: sudo dnf install ${MISSING_PACKAGES[*]}"
            echo "  Arch Linux: sudo pacman -S ${MISSING_PACKAGES[*]}"
            echo "  Alpine Linux: sudo apk add ${MISSING_PACKAGES[*]}"
            echo "  SUSE/openSUSE: sudo zypper install ${MISSING_PACKAGES[*]}"
            echo "  FreeBSD: sudo pkg install ${MISSING_PACKAGES[*]}"
            echo "  OpenBSD: doas pkg_add ${MISSING_PACKAGES[*]}"
            echo "  NetBSD: sudo pkgin install ${MISSING_PACKAGES[*]}"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ System packages installed${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to install system packages${NC}"
        return 1
    fi
}

# Verify Python version
verify_python() {
    echo -e "${YELLOW}Verifying Python installation...${NC}"
    
    if ! command_exists python3; then
        echo -e "${RED}✗ Python 3 not found${NC}"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "Python version: $PYTHON_VERSION"
    
    # Check if version is 3.6+
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 6 ]); then
        echo -e "${RED}✗ Python 3.6+ required (found $PYTHON_VERSION)${NC}"
        return 1
    fi
    
    # Check if venv module is available
    if ! python3 -m venv --help >/dev/null 2>&1; then
        echo -e "${RED}✗ Python venv module not available${NC}"
        echo "Please install python3-venv package"
        return 1
    fi
    
    echo -e "${GREEN}✓ Python version OK${NC}"
    return 0
}

# Create virtual environment
create_venv() {
    echo -e "${YELLOW}Setting up virtual environment...${NC}"
    
    if [ -d "$VENV_PATH" ]; then
        echo "Virtual environment already exists at $VENV_PATH"
        echo "Removing old virtual environment..."
        rm -rf "$VENV_PATH"
    fi
    
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    return 0
}

# Install Python dependencies in venv
install_python_deps() {
    echo -e "${YELLOW}Installing Python dependencies in virtual environment...${NC}"
    
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo -e "${RED}✗ Virtual environment not found${NC}"
        return 1
    fi
    
    # Source venv and get pip path
    source "$VENV_PATH/bin/activate"
    VENV_PIP="$VENV_PATH/bin/pip"
    
    if [ ! -f "$VENV_PIP" ]; then
        echo -e "${RED}✗ pip not found in virtual environment${NC}"
        return 1
    fi
    
    # Upgrade pip first
    echo "Upgrading pip..."
    "$VENV_PIP" install --upgrade pip --quiet
    
    # Install from requirements.txt
    if [ ! -f "$BOT_DIRECTORY/requirements.txt" ]; then
        echo -e "${RED}✗ requirements.txt not found${NC}"
        return 1
    fi
    
    echo "Installing dependencies from requirements.txt..."
    "$VENV_PIP" install -r "$BOT_DIRECTORY/requirements.txt"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python dependencies installed${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to install dependencies${NC}"
        return 1
    fi
}

# Verify installation
verify_installation() {
    echo -e "${YELLOW}Verifying installation...${NC}"
    
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo -e "${RED}✗ Virtual environment not found${NC}"
        return 1
    fi
    
    # Source venv and check modules
    source "$VENV_PATH/bin/activate"
    VENV_PYTHON="$VENV_PATH/bin/python"
    
    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "${RED}✗ Python not found in virtual environment${NC}"
        return 1
    fi
    
    echo "Checking required modules in virtual environment..."
    MISSING=()
    
    "$VENV_PYTHON" -c "import irc" 2>/dev/null || MISSING+=("irc")
    "$VENV_PYTHON" -c "import yaml" 2>/dev/null || MISSING+=("yaml")
    "$VENV_PYTHON" -c "import requests" 2>/dev/null || MISSING+=("requests")
    
    if [ ${#MISSING[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All required modules are installed${NC}"
        
        # Show versions
        echo ""
        echo "Installed packages:"
        "$VENV_PYTHON" -m pip list | grep -E "^(irc|PyYAML|requests)" || true
        
        return 0
    else
        echo -e "${RED}✗ Missing modules: ${MISSING[*]}${NC}"
        return 1
    fi
}

# Main installation
main() {
    echo "============================================================"
    echo "Quizzer IRC Bot - Installation Script"
    echo "============================================================"
    echo ""
    echo "This script will:"
    echo "  1. Check and install required system packages"
    echo "  2. Create a virtual environment (.venv)"
    echo "  3. Install all Python dependencies"
    echo "  4. Verify the installation"
    echo ""
    echo "Note: This bot REQUIRES a virtual environment."
    echo ""
    
    detect_os
    echo "Detected OS: $OS"
    echo ""
    
    # Check sudo access
    check_sudo
    echo ""
    
    # Verify Python
    if ! verify_python; then
        echo -e "${RED}Python verification failed${NC}"
        exit 1
    fi
    echo ""
    
    # Install system packages
    if ! install_system_packages; then
        echo -e "${RED}Failed to install system packages${NC}"
        exit 1
    fi
    echo ""
    
    # Create virtual environment
    if ! create_venv; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    echo ""
    
    # Install Python dependencies
    if ! install_python_deps; then
        echo -e "${RED}Failed to install Python dependencies${NC}"
        exit 1
    fi
    echo ""
    
    # Verify installation
    if ! verify_installation; then
        echo -e "${RED}Installation verification failed${NC}"
        exit 1
    fi
    echo ""
    
    echo "============================================================"
    echo -e "${GREEN}Installation complete!${NC}"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Copy config.yaml.example to config.yaml:"
    echo "     cp config.yaml.example config.yaml"
    echo ""
    echo "  2. Edit config.yaml with your settings"
    echo ""
    echo "  3. Set your NickServ password:"
    echo "     export NICKSERV_PASSWORD='your_password'"
    echo "     # Or use .env file (see SETUP.md)"
    echo ""
    echo "  4. Run the bot:"
    echo "     source .venv/bin/activate"
    echo "     python3 run.py"
    echo ""
    echo "     Or use the management script:"
    echo "     ./tools/startbot.sh start"
    echo ""
    echo "For detailed setup instructions, see SETUP.md"
    echo ""
}

# Run main function
main "$@"
