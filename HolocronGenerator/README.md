# Holocron Generator

Python + PySide6 GUI to author Holocron KB pages and generate SWG output files.

## Features
- Load/Save project (JSON)
- Load from SWG install
- Link insertion + validation + jump
- Move Up/Down reordering
- Category add/remove/rename
- Switch To category behavior
- Generator output (datatables + stf)
- Image support (resource must be `/texture/<name>.dds`)

## Run (dev)
```bash
pip install -r requirements.txt
python main.py
```

## Run (powershell)

#cd to the directory
#run the commands below
- python -m venv .venv
- .\.venv\Scripts\Activate.ps1
- pip install -r requirements.txt

#Once that's done, run the main app
python main.py



## Output
Generates into the selected SWG root:
- `datatables/knowledgebase/<category>.iff`
- `datatables/knowledgebase/filelist.iff`
- `string/<lang>/kb/kb_<category>_n.stf`
- `string/<lang>/kb/kb_<category>_d.stf`


