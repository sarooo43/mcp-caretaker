# Developing on Windows

These steps are for a Windows PowerShell user who already has Python 3.11+ and git.
Run one command per line, in order.

```powershell
git clone https://github.com/sarooo43/mcp-caretaker.git
cd mcp-caretaker
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
```

The last line of pytest output (for example `N passed in X s`) is all the owner needs
to report. Nothing else in the output needs to be copied.
