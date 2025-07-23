# Environment Setup Instructions

## Python Virtual Environment Configuration

### Prerequisites
- Python 3.9+ (Current system: Python 3.10.12 ✅)
- pip package manager
- python3-venv package (for Ubuntu/Debian)

### Virtual Environment Setup

#### 1. Install Required System Packages (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10-venv
```

#### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Verify creation
ls -la .venv/
```

#### 3. Activate Virtual Environment

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

#### 4. Verify Environment Isolation
```bash
# Should show virtual environment Python
which python
python --version

# Should show virtual environment pip
which pip
pip --version
```

#### 5. Environment Deactivation
```bash
deactivate
```

### Environment Verification

After activation, verify the environment:

```bash
# Check Python version
python --version

# Check pip version  
pip --version

# Verify virtual environment is active (should show .venv path)
echo $VIRTUAL_ENV
```

### Activation Commands Reference

**Bash/Zsh:**
```bash
source .venv/bin/activate
```

**Fish:**
```bash
source .venv/bin/activate.fish
```

**PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
.venv\Scripts\activate.bat
```

### Troubleshooting

#### Virtual Environment Creation Fails
- Ensure python3-venv package is installed
- Check Python version compatibility (3.9+)
- Verify sufficient disk space

#### Activation Fails
- Check virtual environment was created successfully
- Verify correct path to activation script
- Ensure shell supports source command

#### Dependencies Installation Issues
- Ensure virtual environment is activated
- Check internet connectivity
- Verify pip is up to date: `pip install --upgrade pip`

### Environment Management Best Practices

1. **Always activate virtual environment before working**
2. **Keep requirements files updated**
3. **Use absolute paths when documenting setup**
4. **Test environment setup on clean systems**
5. **Document all system dependencies**

### Integration with Development Tools

The virtual environment integrates with:
- **IDE/Editor**: Configure to use .venv/bin/python
- **Testing**: pytest will use virtual environment
- **Code Quality**: mypy, black, ruff use virtual environment
- **Git**: .venv/ is ignored in .gitignore