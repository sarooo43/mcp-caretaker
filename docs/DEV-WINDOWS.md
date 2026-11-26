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

## Step 7: try the check command once

NOT VERIFIED until the owner runs it. Run one command per line, in order.
Use absolute paths for the venv interpreter and the fixture script, and keep
the report files in the current folder.

```powershell
$py = (Resolve-Path .venv\\Scripts\\python.exe).Path
$server = (Resolve-Path examples\\servers\\clean_server.py).Path
& $py -m mcp_caretaker check --trust --json report.json --markdown report.md -- $py $server
```

Expected: exit code 0, 25 `[PASS]` lines, and `report.json` plus `report.md`
in the current folder. A pass is not a safety guarantee. Running a server
executes its code; this tool is not a sandbox.

## Releasing

The release steps, including the build and upload commands and the README lines
that change after the first upload, are in [RELEASING.md](RELEASING.md). They
are run by the owner, not by an agent, and no token goes into the repository.
