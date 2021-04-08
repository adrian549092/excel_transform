# excel-transform

[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-388/)
[![PyPI](https://img.shields.io/pypi/v/excel-transform.svg)](https://pypi.python.org/pypi/excel-transform)
[![Downloads](https://pepy.tech/badge/excel-transform)](https://pepy.tech/project/excel-transform)
![GitHub contributors](https://img.shields.io/github/contributors/adrian549092/excel-transform.svg)

### Installation
Make sure you are using [python](https://www.python.org/downloads/) 3.8+.
```
λ python --version
```
>Python 3.8.8

Create a virtual environment in the desired directory.
```
λ mkdir ~/excel-transform
λ cd ~/excel-transform
λ python -m venv venv
```
Activate the virtual environment and install dependencies.

**Windows:**
```
λ venv\Scripts\activate.bat
```

**Unix/Linux:**
```
λ source venv/bin/activate
```
**Install Option 1 (Recommended):**

```
(venv) λ pip install excel-transform
```
**Install Option 2:**

Install from source via `github`
```
(venv) λ pip install git+https://github.com/adrian549092/excel-transform.git@master
```

### Create template mapping file
Run this command to generate the skeleton of a mapping file
```
(venv) λ excel-transform mapping-skeleton -o some_mapping.json
```

### Transform Spreadsheet
Transform a spreadsheet
```
(venv) λ excel-transform transform -o transformed.xlsx some_spreadsheet.xlsx mapping.json
```

### Transform GUI
Launch available PYQT5 GUI
```
(venv) λ excel-transform gui
```

### Get Help
Use the `--help` flag anywhere along the `excel-transform` commands to get context aware help
```
(venv) λ excel-transform --help
```
```
(venv) λ excel-transform transform --help
```
