# Getting Started with waterlib

A step-by-step guide for water resources consultants to build, run, and visualize water system models.

## Table of Contents

1. [Initial Setup](#initial-setup)
   - [Prerequisites](#prerequisites)
   - [Setting Up Your Project Folder](#setting-up-your-project-folder)
   - [Creating a Python Virtual Environment](#creating-a-python-virtual-environment)
2. [Installation](#installation)
3. [Your First Model](#your-first-model)
   - [Option A: Using Project Scaffolding (Recommended)](#option-a-using-project-scaffolding-recommended)
   - [Option B: Building from Scratch](#option-b-building-from-scratch)
3. [The Live Model Watcher: Recommended Workflow](#the-live-model-watcher-recommended-workflow) ⭐
4. [Understanding the YAML Structure](#understanding-the-yaml-structure)
5. [Working with Climate Data](#working-with-climate-data)
6. [Building Complex Models](#building-complex-models)
7. [Analyzing Results](#analyzing-results)
8. [Creating Visualizations](#creating-visualizations)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
    - [Project Scaffolding Issues](#project-scaffolding-issues)
    - [Common Model Errors](#common-model-errors)

## Initial Setup

Before installing waterlib, let's set up your development environment properly. This ensures you have a clean, isolated workspace for your water modeling projects.

### Prerequisites

#### Install Python

waterlib requires Python 3.9 or later. We recommend using the latest stable version of Python to ensure you have the most recent features and security updates.

**Check if Python is installed:**

```bash
python --version
```

or on some systems:

```bash
python3 --version
```

**If Python is not installed or you have an older version:**

- **Windows**: Download from [python.org](https://www.python.org/downloads/) and run the installer
  - ✅ Check "Add Python to PATH" during installation
  - ✅ Choose "Install for all users" if you have admin rights

- **macOS**:
  ```bash
  # Using Homebrew (recommended)
  brew install python

  # Or download from python.org
  ```

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-venv
  ```

- **Linux (Fedora/RHEL)**:
  ```bash
  sudo dnf install python3 python3-pip
  ```

**Verify installation:**

```bash
python --version
# Should show: Python 3.9.x or higher
```

### Setting Up Your Project Folder

waterlib is currently a local development project. You'll need to get the source code and set up your environment to use it.

#### Getting the waterlib Source Code

**Current Setup (Local Development):**

The waterlib source code is located at:
```
C:\Users\JasonLillywhite\source\repos\waterlib
```

If you're working on a different machine or want to set up your own copy:

**1. Create a parent folder for your development projects:**

```bash
# Windows
mkdir C:\Users\YourName\source\repos
cd C:\Users\YourName\source\repos

# macOS/Linux
mkdir -p ~/source/repos
cd ~/source/repos
```

**2. Copy or clone the waterlib folder to this location**

Your folder structure will look like:

```
source/
└── repos/
    └── waterlib/               # The waterlib project
        ├── waterlib/           # Source code
        ├── examples/           # Example models
        ├── tests/              # Test suite
        ├── docs/               # Documentation
        └── venv/               # Virtual environment (you'll create this)
```

#### Future GitHub Workflow

Once waterlib is hosted on GitHub, you'll be able to clone it directly:

```bash
# Future command (not yet available)
cd C:\Users\YourName\source\repos
git clone https://github.com/yourusername/waterlib.git
cd waterlib
```

**For now, work with the existing local copy at `C:\Users\JasonLillywhite\source\repos\waterlib`.**

### Creating a Python Virtual Environment

A virtual environment is an isolated Python environment that keeps your project dependencies separate from your system Python. This is a best practice that prevents version conflicts and makes your project reproducible.

#### Why Use a Virtual Environment?

- ✅ **Isolation**: Each project has its own dependencies
- ✅ **Reproducibility**: Easy to recreate the exact environment
- ✅ **No conflicts**: Different projects can use different package versions
- ✅ **Clean system**: Doesn't clutter your system Python installation

#### Creating the Virtual Environment

**1. Navigate to the waterlib project folder:**

```bash
cd C:\Users\JasonLillywhite\source\repos\waterlib
```

**2. Create the virtual environment:**

```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

This creates a folder called `venv` inside the waterlib directory containing an isolated Python environment.

**3. Activate the virtual environment:**

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

**You'll know it's activated when you see `(venv)` at the start of your command prompt:**

```bash
(venv) C:\Users\JasonLillywhite\source\repos\waterlib>
```

**4. Upgrade pip (recommended):**

```bash
python -m pip install --upgrade pip
```

#### Deactivating the Virtual Environment

When you're done working, deactivate the environment:

```bash
deactivate
```

The `(venv)` prefix will disappear from your prompt.

#### Using the Virtual Environment

**Every time you work on waterlib:**

1. Open a terminal/command prompt
2. Navigate to the waterlib folder: `cd C:\Users\JasonLillywhite\source\repos\waterlib`
3. Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
4. Work on your project
5. Deactivate when done: `deactivate`

**Tip:** Keep the terminal open while working to avoid reactivating repeatedly.

#### Troubleshooting Virtual Environments

**PowerShell execution policy error (Windows):**

If you get an error about execution policies when activating:

```powershell
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Wrong Python version in virtual environment:**

If `python --version` shows the wrong version after activation:

```bash
# Recreate the virtual environment with a specific Python version
python3.11 -m venv venv  # Replace 3.11 with your desired version
```

**Virtual environment not activating:**

- Make sure you're in the correct directory
- Check that the `venv` folder exists
- Try using the full path to the activate script

### Your Setup Checklist

Before proceeding to installation, verify:

- ✅ Python 3.9+ is installed: `python --version`
- ✅ You have a project folder created
- ✅ Virtual environment is created: `venv` folder exists
- ✅ Virtual environment is activated: `(venv)` appears in prompt
- ✅ pip is up to date: `python -m pip install --upgrade pip`

**You're now ready to install waterlib!**

## Installation

**Important:** Make sure your virtual environment is activated before installing waterlib. You should see `(venv)` in your command prompt.

### Installation Workflows

There are two ways to use waterlib depending on your role:

1. **End-User Workflow**: Building water models in your own project folders
2. **Developer Workflow**: Modifying waterlib source code

#### End-User Workflow (Building Models)

If you're building water models and want to use waterlib as a library, follow these steps:

**1. Create your project folder:**

```bash
# Create a folder for your water modeling projects
mkdir C:\Users\JasonLillywhite\waterlib_projects
cd C:\Users\JasonLillywhite\waterlib_projects

# Create a specific project
mkdir my_reservoir_model
cd my_reservoir_model
```

**2. Create a virtual environment in your project folder:**

```bash
# Windows
python -m venv .venv

# Activate it
.venv\Scripts\activate
```

**3. Install waterlib from the source directory:**

```bash
# Install waterlib from the local source (with visualization support)
pip install -e "C:\Users\JasonLillywhite\source\repos\waterlib[viz]"
```

**Important:** Notice the path points to the waterlib source directory, not your current directory!

**4. Verify the installation:**

```bash
python -c "import waterlib; print(waterlib.__version__)"
```

**5. Start building your model:**

```bash
# Use waterlib to create a project scaffold
python -c "import waterlib; waterlib.create_project('my_model')"

# Or create your own YAML files and Python scripts
```

**Your folder structure will look like:**

```
waterlib_projects/
└── my_reservoir_model/
    ├── .venv/                  # Virtual environment for this project
    ├── my_model/               # Generated by create_project()
    │   ├── models/
    │   ├── data/
    │   └── ...
    └── custom_script.py        # Your custom scripts
```

**Every time you work on this project:**

```bash
cd C:\Users\JasonLillywhite\waterlib_projects\my_reservoir_model
.venv\Scripts\activate
python custom_script.py
```

#### Developer Workflow (Modifying waterlib)

If you're working on the waterlib source code itself, follow these steps:

**1. Navigate to the waterlib source directory:**

```bash
cd C:\Users\JasonLillywhite\source\repos\waterlib
```

**2. Activate the virtual environment:**

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

**3. Install waterlib in editable mode with all dependencies:**

```bash
# Install with development and visualization dependencies
pip install -e ".[dev,viz]"
```

This command:
- `-e` installs in "editable" mode (changes to source code take effect immediately)
- `.[dev,viz]` installs waterlib plus development tools and visualization libraries

**4. Verify the installation:**

```python
python -c "import waterlib; print(waterlib.__version__)"
```

You should see the version number printed (e.g., `0.1.0`).

**5. Make changes and run tests:**

```bash
# Run tests
pytest

# Make changes to source code
# Changes take effect immediately (no reinstall needed)
```

### Quick Reference

**For end-users building models:**
```bash
# In your project directory
cd C:\Users\JasonLillywhite\waterlib_projects\my_project
python -m venv .venv
.venv\Scripts\activate
pip install -e "C:\Users\JasonLillywhite\source\repos\waterlib[viz]"
```

**For developers working on waterlib:**
```bash
# In the waterlib source directory
cd C:\Users\JasonLillywhite\source\repos\waterlib
venv\Scripts\activate
pip install -e ".[dev,viz]"
```

### What Gets Installed

The installation includes:

**Core dependencies:**
- `numpy` - Numerical computing
- `pandas` - Data manipulation
- `pyyaml` - YAML file parsing

**Visualization dependencies (`[viz]`):**
- `matplotlib` - Plotting
- `networkx` - Network diagrams

**Development dependencies (`[dev]`):**
- `pytest` - Testing framework
- `hypothesis` - Property-based testing
- `pytest-cov` - Code coverage

### Future Installation (Once on PyPI)

Once waterlib is published to PyPI, users will be able to install it with:

```bash
# Basic installation (future)
pip install waterlib

# With visualization support (future)
pip install waterlib[viz]
```

### Troubleshooting Installation

**"neither 'setup.py' nor 'pyproject.toml' found" error:**

This happens when you try to install waterlib from the wrong directory. You need to specify the path to the waterlib source code:

```bash
# ❌ Wrong - trying to install from current directory
pip install -e ".[viz]"

# ✅ Correct - install from waterlib source directory
pip install -e "C:\Users\JasonLillywhite\source\repos\waterlib[viz]"
```

**"pip: command not found":**
- Make sure your virtual environment is activated
- Try `python -m pip install -e "C:\Users\JasonLillywhite\source\repos\waterlib[viz]"` instead

**Permission errors:**
- Don't use `sudo` - you should be in a virtual environment
- Make sure you have write permissions to the waterlib directory

**Package conflicts:**
- If you get dependency conflicts, try creating a fresh virtual environment:
  ```bash
  deactivate
  rm -rf .venv  # or rmdir /s .venv on Windows
  python -m venv .venv
  .venv\Scripts\activate
  pip install -e "C:\Users\JasonLillywhite\source\repos\waterlib[viz]"
  ```

**Import errors after installation:**
- Make sure your virtual environment is activated
- Verify waterlib is installed: `pip list | findstr waterlib`
- Try importing in Python: `python -c "import waterlib; print(waterlib.__version__)"`

**Changes to waterlib source code not taking effect:**
- If you installed with `-e` (editable mode), changes should be immediate
- If not, you may need to reinstall: `pip install -e "C:\Users\JasonLillywhite\source\repos\waterlib[viz]" --force-reinstall --no-deps`

## Your First Model

You have two options for creating your first model:
1. **Use project scaffolding** (recommended for beginners) - Get a working project in seconds
2. **Build from scratch** - Learn the YAML structure step by step

### Option A: Using Project Scaffolding (Recommended)

The fastest way to get started is using the `create_project()` function, which generates a complete working project with examples.

#### Step 1: Create a New Project

```python
import waterlib

# Create a new project with working examples
project_path = waterlib.create_project("my_first_model")
print(f"Created project at: {project_path}")
```

This creates a complete project structure:

```
my_first_model/
├── README.md                    # Project documentation
├── models/
│   └── baseline.yaml            # Working model configuration
├── data/
│   ├── wgen_params.csv          # Weather generator parameters
│   ├── climate_timeseries.csv   # Example climate data
│   └── README.md                # Data documentation
├── outputs/                     # Results directory
├── config/                      # Configuration directory
└── run_model.py                 # Sample Python script
```

#### Step 2: Run the Example Model

Navigate to your project and run the included script:

```bash
cd my_first_model
python run_model.py
```

You'll see output like:

```
Loading model...
Running simulation...
Running simulation: 100%|██████████| 365/365 [00:02<00:00, 156.23 timesteps/s]

Simulation complete!
Simulated 365 days

Reservoir storage statistics:
  Mean: 2847392 m³
  Min:  1523891 m³
  Max:  4123456 m³

Saving results...
Plots saved to: outputs/simulation_plots.png

Done!
```

#### Step 3: Explore and Modify

Open `models/baseline.yaml` in your text editor and explore the model structure. Try modifying:

- Reservoir capacity: Change `max_storage_m3`
- Population: Change `population` in the demand component
- Catchment area: Change `area_km2` in the catchment

Save your changes and run `python run_model.py` again to see the effects!

#### Creating Different Project Types

**Minimal project (no examples):**
```python
# Just the directory structure
waterlib.create_project("minimal_model", include_examples=False)
```

**Project in specific location:**
```python
# Create in a custom directory
waterlib.create_project(
    "regional_model",
    parent_dir="/projects/water_resources"
)
```

**Overwrite existing project:**
```python
# Replace existing project (careful!)
waterlib.create_project("my_model", overwrite=True)
```

### Option B: Building from Scratch

If you want to learn the YAML structure from the ground up, follow these steps to build a simple catchment-reservoir-demand system.

### Step 1: Create the YAML File

Create a file called `first_model.yaml`:

```yaml
name: "My First Water Model"
description: "A simple catchment feeding a reservoir serving a city"

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: 'wgen'
    temperature:
      mode: 'wgen'
    et_method: 'hargreaves'

    wgen_config:
      param_file: '../data/wgen_params.csv'
      latitude: 40.5
      elevation_m: 500.0
      # Temperature parameters (°C)
      txmd: 20.0    # Mean daily max temp (dry days)
      txmw: 18.0    # Mean daily max temp (wet days)
      tn: 5.0       # Mean daily min temp
      atx: 10.0     # Amplitude of max temp variation
      atn: 8.0      # Amplitude of min temp variation
      cvtx: 0.15    # Coefficient of variation for max temp
      acvtx: 0.02   # Amplitude of CV variation for max temp
      cvtn: 0.18    # Coefficient of variation for min temp
      acvtn: 0.02   # Amplitude of CV variation for min temp
      dt_day: 0.0   # Daily temperature adjustment
      # Solar radiation parameters
      rs_mean: 15.0
      rs_amplitude: 8.0
      rs_cv: 0.25
      rs_wet_factor: 0.7
      min_rain_mm: 0.1
      seed: 42

components:
  catchment:
    type: Catchment
    area_km2: 100.0
    snow17_params:
      scf: 1.0
      mfmax: 1.5
    awbm_params:
      c_vec: [0.134, 0.433, 0.433]
      a_vec: [0.279, 0.514, 0.207]
      kbase: 0.95
      ksurf: 0.35

  reservoir:
    type: Reservoir
    initial_storage: 2000000
    max_storage: 5000000
    surface_area: 500000
    inflows:
      - catchment.runoff

  demand:
    type: Demand
    source: reservoir
    mode: municipal
    population: 50000
    per_capita_demand_lpd: 200
```

### Step 2: Run the Simulation

Create a Python script `run_model.py`:

```python
import waterlib

# Load the model
model = waterlib.load_model('first_model.yaml')

# Run the simulation
results = waterlib.run_simulation(
    model,
    output_dir='./results',
    generate_plots=True
)

# Print summary statistics
print(f"Simulation complete!")
print(f"Mean reservoir storage: {results.dataframe['reservoir.storage'].mean():,.0f} m³")
print(f"Total demand supplied: {results.dataframe['demand.supplied'].sum():,.0f} m³")
print(f"Total deficit: {results.dataframe['demand.deficit'].sum():,.0f} m³")
```

### Step 3: Run It

```bash
python run_model.py
```

You'll see output like:

```
Simulation complete!
Mean reservoir storage: 2,847,392 m³
Total demand supplied: 3,650,000 m³
Total deficit: 0 m³
```

And find these files in `./results/`:
- `simulation_results.csv` - Complete time series data
- `model_network.png` - Network diagram (if `generate_plots=True`)

**Congratulations!** You've just built and run your first water system model.

## The Live Model Watcher: Recommended Workflow

Now that you've run your first model, let's learn the **recommended way to build models**: the Live Model Watcher.

### What is the Live Model Watcher?

The Live Model Watcher is a Jupyter notebook that monitors your YAML file and automatically updates the visualization whenever you save changes. This creates a powerful split-screen workflow:

```
┌─────────────────────────┬─────────────────────────┐
│   Text Editor           │   Jupyter Notebook      │
│   (Edit YAML)           │   (Live Visualization)  │
│                         │                         │
│  components:            │   [Network Diagram]     │
│    reservoir:           │                         │
│      type: Reservoir    │   Updates automatically │
│      meta:              │   when you save!        │
│        x: 0.5           │                         │
│        y: 0.5           │                         │
└─────────────────────────┴─────────────────────────┘
```

### Why Use the Live Watcher?

The Live Watcher is perfect for:

- **Learning waterlib**: See how YAML changes affect the model structure
- **Iterative design**: Quickly experiment with different layouts
- **Visual debugging**: Immediately verify connections are correct
- **Client presentations**: Build models live during meetings
- **Blog posts and tutorials**: Design models while writing about them

### Getting Started

1. **Navigate to examples directory**:
   ```bash
   cd examples
   ```

2. **Start Jupyter**:
   ```bash
   jupyter notebook live_view.ipynb
   ```

3. **Run all cells** in the notebook (Cell → Run All)

4. **Open a YAML file** in your text editor side-by-side with Jupyter

5. **Edit and save** - watch the magic happen!

### What You Can Change

The Live Watcher automatically updates when you modify:

- **Component positions**: Change `meta.x` and `meta.y` values
- **Component colors**: Try different `meta.color` values
- **Component labels**: Update `meta.label` text
- **Add/remove components**: See the structure change instantly
- **Modify connections**: Verify flow paths are correct
- **Change parameters**: See how it affects the model

### Example: Designing a Layout

Let's use the Live Watcher to design a nice layout for our first model.

**Step 1**: Start with a basic model (no meta blocks):

```yaml
components:
  catchment:
    type: Catchment
    area_km2: 100.0
    # ... parameters ...

  reservoir:
    type: Reservoir
    # ... parameters ...

  demand:
    type: Demand
    # ... parameters ...
```

The Live Watcher shows default positions (probably overlapping).

**Step 2**: Add vertical positioning (top to bottom flow):

```yaml
components:
  catchment:
    type: Catchment
    area_km2: 100.0
    # ... parameters ...
    meta:
      x: 0.5    # Center horizontally
      y: 0.8    # Near top

  reservoir:
    type: Reservoir
    # ... parameters ...
    meta:
      x: 0.5    # Center horizontally
      y: 0.5    # Middle

  demand:
    type: Demand
    # ... parameters ...
    meta:
      x: 0.5    # Center horizontally
      y: 0.2    # Near bottom
```

Save → See the components align vertically!

**Step 3**: Add colors to distinguish component types:

```yaml
components:
  catchment:
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'  # Light green for catchment

  reservoir:
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.5
      color: '#4169E1'  # Royal blue for reservoir

  demand:
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.2
      color: '#FF6347'  # Tomato red for demand
```

Save → See the colors update!

**Step 4**: Add descriptive labels:

```yaml
components:
  catchment:
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'
      label: 'Mountain Catchment'  # Descriptive label

  reservoir:
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.5
      color: '#4169E1'
      label: 'Main Reservoir'

  demand:
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.2
      color: '#FF6347'
      label: 'City Water Supply'
```

Save → See the labels appear!

### Tips for Using the Live Watcher

**Layout Tips:**
- Use `y` values from 0.9 (top) to 0.1 (bottom) for top-to-bottom flow
- Use `x` values from 0.1 (left) to 0.9 (right) for left-to-right flow
- Space components evenly: 0.2, 0.4, 0.6, 0.8
- Keep similar components at the same vertical level

**Color Tips:**
- Use consistent colors for component types:
  - Green (`#90EE90`) for catchments
  - Blue (`#4169E1`) for reservoirs
  - Red (`#FF6347`) for demands
  - Orange (`#FFA500`) for pumps
  - Gray (`#A9A9A9`) for junctions

**Workflow Tips:**
- Start with positions, then add colors, then add labels
- Save frequently to see incremental changes
- Keep the YAML file simple while learning
- Use the manual refresh cell if auto-update is too fast

### When to Use Live Watcher vs. Regular Notebooks

**Use Live Watcher for:**
- Model design and layout
- Learning waterlib
- Experimenting with structure
- Creating diagrams for presentations

**Use regular notebooks for:**
- Running simulations
- Analyzing results
- Creating time series plots
- Production workflows

### Next Steps with Live Watcher

1. **Try the example models**:
   - Open `simple_reservoir.yaml` in the Live Watcher
   - Modify positions and see changes
   - Try different color schemes

2. **Build your own model**:
   - Start with one component
   - Add components one at a time
   - Position and style as you go

3. **Create presentation-ready diagrams**:
   - Design the perfect layout
   - Export the diagram (the notebook saves it automatically)
   - Use in reports and presentations

The Live Model Watcher is the fastest way to become proficient with waterlib. Spend 30 minutes experimenting with it, and you'll understand the YAML structure intuitively.

## Understanding the YAML Structure

A waterlib YAML file has three main sections:

### 1. Model Metadata (Optional)

```yaml
name: "Model Name"
description: "What this model represents"
```

This is for documentation purposes and appears in visualizations.

### 2. Settings (Required)

```yaml
settings:
  # Simulation period
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  # Climate configuration
  climate:
    # ... climate settings ...

  # Visualization settings (optional)
  visualization:
    figure_size: [12, 8]
```

**Key points:**
- Dates must be in `YYYY-MM-DD` format
- Climate settings control global utilities (precipitation, temperature, ET)
- Visualization settings control network diagram appearance

### 3. Components (Required)

```yaml
components:
  component_name:
    type: ComponentType
    # Component-specific parameters
    param1: value1
    param2: value2
    # Visualization metadata (optional)
    meta:
      x: 0.5
      y: 0.5
      color: '#90EE90'
      label: 'Display Name'
```

**Key points:**
- Each component needs a unique name
- `type` must be one of the available component types
- Parameters vary by component type
- `meta` dictionary controls visualization (optional)

## Working with Climate Data

waterlib uses the WGEN weather generator for synthetic climate data.

### WGEN Mode (Weather Generator)

Perfect for planning studies and scenario analysis:

```yaml
settings:
  climate:
    precipitation:
      mode: 'wgen'
    temperature:
      mode: 'wgen'
    et_method: 'hargreaves'

    wgen_config:
      param_file: 'data/wgen_params.csv'  # Monthly precipitation parameters
      latitude: 40.5
      elevation_m: 500.0

      # Temperature parameters (°C)
      txmd: 20.0    # Mean daily max temp (dry days)
      txmw: 18.0    # Mean daily max temp (wet days)
      tn: 5.0       # Mean daily min temp
      atx: 10.0     # Amplitude of max temp variation
      atn: 8.0      # Amplitude of min temp variation
      cvtx: 0.15    # Coefficient of variation for max temp
      acvtx: 0.02   # Amplitude of CV variation for max temp
      cvtn: 0.18    # Coefficient of variation for min temp
      acvtn: 0.02   # Amplitude of CV variation for min temp
      dt_day: 0.0   # Daily temperature adjustment

      # Solar radiation parameters
      rs_mean: 15.0
      rs_amplitude: 8.0
      rs_cv: 0.25
      rs_wet_factor: 0.7
      min_rain_mm: 0.1
      seed: 42      # For reproducibility (optional)
```

**WGEN Parameters File:**

The `param_file` must be a CSV with monthly precipitation parameters:

```csv
# WGEN Monthly Precipitation Parameters
Month,PWW,PWD,ALPHA,BETA
1,0.60,0.25,2.0,10.0
2,0.58,0.23,2.1,11.0
3,0.62,0.28,2.2,12.0
# ... (12 rows total, one per month)
```

Columns:
- **Month**: Month number (1-12)
- **PWW**: Probability of wet day after wet day
- **PWD**: Probability of wet day after dry day
- **ALPHA**: Gamma distribution alpha parameter
- **BETA**: Gamma distribution beta parameter

### Timeseries Mode (Historical Data)

Use actual climate data from CSV files:

```yaml
settings:
  climate:
    precipitation:
      mode: 'timeseries'
      file: 'data/precip.csv'
      column: 'precip_mm'
      date_column: 'date'

    temperature:
      mode: 'timeseries'
      file: 'data/temp.csv'
      tmin_column: 'tmin_c'
      tmax_column: 'tmax_c'
      date_column: 'date'

    et_method: 'hargreaves'
    latitude: 40.5
```

**CSV file format:**
```csv
date,precip_mm,tmin_c,tmax_c
2020-01-01,5.2,3.1,12.4
2020-01-02,0.0,4.2,14.1
2020-01-03,12.8,2.8,10.9
...
```

**Key points:**
- File paths are relative to the YAML file location
- Date column must be parseable by pandas (YYYY-MM-DD recommended)
- You can mix modes (e.g., WGEN precip with timeseries temperature)

### Why Climate Drivers?

In waterlib, climate data is provided through a **DriverRegistry** system that makes climate data available to all components without explicit connections. This means:

**Clean and simple:**
```yaml
settings:
  climate:
    precipitation:
      mode: 'wgen'
    wgen_config:
      param_file: 'data/wgen_params.csv'
      latitude: 40.5
      # ... other parameters ...

components:
  catchment:
    type: Catchment
    # Automatically receives precipitation from climate drivers!
```

The DriverRegistry system provides:
- **Centralized climate data**: All components access the same climate time series
- **Consistent interface**: Components use `drivers.get('precipitation')`, `drivers.get('temperature')`, etc.
- **Clean models**: No need to wire climate data to every component
- **Flexible sources**: Support for timeseries files, WGEN, or custom drivers

This keeps your models cleaner and more maintainable.

## Building Complex Models

Let's build a more realistic model step by step.

### Step 1: Multiple Catchments

```yaml
components:
  upper_catchment:
    type: Catchment
    area_km2: 150.0
    # ... parameters ...

  lower_catchment:
    type: Catchment
    area_km2: 80.0
    # ... parameters ...

  river_junction:
    type: Junction
    inflows:
      - upper_catchment.runoff_m3d
      - lower_catchment.runoff_m3d
```

### Step 2: Add River Diversion

```yaml
components:
  # ... catchments and junction ...

  irrigation_diversion:
    type: RiverDiversion
    max_diversion_m3d: 50000
    priority: 1
    source: river_junction

  farm_demand:
    type: Demand
    source: irrigation_diversion
    mode: agricultural
    irrigated_area_ha: 500
    crop_coefficient: 0.8
```

### Step 3: Add Reservoir and Municipal Demand

```yaml
components:
  # ... previous components ...

  main_reservoir:
    type: Reservoir
    initial_storage_m3: 2500000
    max_storage_m3: 5000000
    surface_area_m2: 600000
    spillway_elevation_m: 245.0
    inflows:
      - irrigation_diversion.remaining_flow_m3d

  pump_station:
    type: Pump
    mode: constant
    max_capacity_m3d: 100000
    source: main_reservoir

  city_demand:
    type: Demand
    source: pump_station
    mode: municipal
    population: 75000
    per_capita_demand_lpd: 220
```

### Step 4: Add Visualization Metadata

```yaml
components:
  upper_catchment:
    type: Catchment
    area_km2: 150.0
    # ... parameters ...
    meta:
      x: 0.3
      y: 0.9
      color: '#90EE90'
      label: 'Upper Catchment'

  lower_catchment:
    type: Catchment
    area_km2: 80.0
    # ... parameters ...
    meta:
      x: 0.7
      y: 0.9
      color: '#98FB98'
      label: 'Lower Catchment'

  # ... add meta to all components ...
```

**Positioning tips:**
- Use `y` values from 0.9 (top) to 0.1 (bottom) to show flow direction
- Space components horizontally with `x` values from 0.1 to 0.9
- Use consistent colors for similar component types
- Keep labels short and descriptive

## Analyzing Results

The `Results` object provides multiple ways to analyze simulation outputs.

### Access the DataFrame

```python
results = waterlib.run_simulation(model)

# Get the complete DataFrame
df = results.dataframe

# Access specific outputs
reservoir_storage = df['reservoir.storage']
catchment_runoff = df['catchment.runoff_m3d']
demand_deficit = df['demand.deficit']
```

### Calculate Statistics

```python
# Mean values
mean_storage = df['reservoir.storage'].mean()
mean_runoff = df['catchment.runoff_m3d'].mean()

# Maximum/minimum
max_storage = df['reservoir.storage'].max()
min_storage = df['reservoir.storage'].min()

# Sum (for cumulative values)
total_supplied = df['demand.supplied'].sum()
total_deficit = df['demand.deficit'].sum()

# Reliability
reliability = total_supplied / (total_supplied + total_deficit) * 100

print(f"Demand reliability: {reliability:.1f}%")
```

### Time-Based Analysis

```python
# Monthly aggregation
monthly = df.resample('M').mean()

# Seasonal analysis
winter = df[df.index.month.isin([12, 1, 2])]
summer = df[df.index.month.isin([6, 7, 8])]

print(f"Winter mean storage: {winter['reservoir.storage'].mean():,.0f} m³")
print(f"Summer mean storage: {summer['reservoir.storage'].mean():,.0f} m³")
```

### Export Results

```python
# Export to CSV
results.to_csv('./results/simulation_results.csv')

# Export specific columns
df[['reservoir.storage', 'demand.supplied']].to_csv('./results/key_metrics.csv')

# Export monthly summary
monthly.to_csv('./results/monthly_summary.csv')
```

### Get Component-Specific Outputs

```python
# Get all outputs for a specific component
reservoir_outputs = results.get_component_output('reservoir')

# Access specific output
storage = results.get_component_output('reservoir', 'storage')
```

## Creating Visualizations

waterlib provides two types of visualizations: network diagrams and time series plots.

### Network Diagrams

```python
import waterlib

model = waterlib.load_model('my_model.yaml')

# Create network diagram
model.visualize(output_path='./results/model_network.png')
```

**Customization:**
```python
# Custom figure size
model.visualize(
    output_path='./results/model_network.png',
    figsize=(16, 12)
)

# Display interactively (don't save)
model.visualize(output_path=None, show=True)
```

**Tips for better diagrams:**
- Use the `meta` dictionary to position nodes explicitly
- Group related components vertically (same `x` value)
- Use colors to distinguish component types
- Keep labels concise

### Time Series Plots

```python
results = waterlib.run_simulation(model)

# Single variable
results.plot(
    outputs=['reservoir.storage'],
    title='Reservoir Storage Over Time',
    filename='./results/storage.png'
)

# Multiple variables (same scale)
results.plot(
    outputs=['reservoir.storage', 'reservoir.elevation'],
    title='Reservoir State',
    filename='./results/reservoir_state.png'
)

# Dual-axis plot (different scales)
results.plot(
    outputs=['reservoir.storage'],
    secondary_outputs=['catchment.runoff_m3d'],
    title='Storage and Runoff',
    filename='./results/storage_vs_runoff.png'
)

# Multiple variables on each axis
results.plot(
    outputs=['reservoir.storage', 'reservoir.elevation'],
    secondary_outputs=['catchment.runoff_m3d', 'demand.supplied'],
    title='Comprehensive Analysis',
    filename='./results/comprehensive.png'
)
```

### Custom Plots with Matplotlib

For more control, use matplotlib directly:

```python
import matplotlib.pyplot as plt

df = results.dataframe

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(df.index, df['reservoir.storage'] / 1e6, label='Storage')
ax.axhline(y=2.0, color='r', linestyle='--', label='Target')
ax.set_xlabel('Date')
ax.set_ylabel('Storage (million m³)')
ax.set_title('Reservoir Storage with Target Level')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('./results/custom_plot.png', dpi=300)
plt.close()
```

## Best Practices

### Model Organization

1. **Use descriptive component names**
   ```yaml
   # Good
   upper_mountain_catchment:
     type: Catchment

   # Avoid
   c1:
     type: Catchment
   ```

2. **Add comments to your YAML**
   ```yaml
   components:
     # Upper catchment with snow processes
     upper_catchment:
       type: Catchment
       area_km2: 150.0  # Drainage area in square kilometers
   ```

3. **Group related components**
   ```yaml
   components:
     # ========== CATCHMENTS ==========
     upper_catchment:
       # ...
     lower_catchment:
       # ...

     # ========== STORAGE ==========
     main_reservoir:
       # ...
   ```

### Parameter Selection

1. **Start with default parameters**
   - Use standard AWBM parameters: `c1: 0.134, c2: 0.433, c3: 0.433`
   - Use standard Snow17 parameters from examples

2. **Calibrate if you have observed data**
   - Compare simulated vs. observed runoff
   - Adjust parameters systematically
   - Document your calibration process

3. **Document parameter sources**
   ```yaml
   catchment:
     type: Catchment
     area_km2: 150.0
     # Parameters calibrated to USGS gauge 12345678 (2015-2020)
     awbm_params:
       c1: 0.145  # Calibrated value
   ```

### File Organization

```
project/
├── models/
│   ├── baseline.yaml
│   ├── scenario_1.yaml
│   └── scenario_2.yaml
├── data/
│   ├── precip.csv
│   ├── temp.csv
│   └── reservoir_eav.csv
├── scripts/
│   ├── run_baseline.py
│   ├── run_scenarios.py
│   └── analyze_results.py
└── results/
    ├── baseline/
    ├── scenario_1/
    └── scenario_2/
```

### Version Control

1. **Track your YAML files in git**
   ```bash
   git add models/*.yaml
   git commit -m "Add baseline model"
   ```

2. **Don't track results**
   ```
   # .gitignore
   results/
   *.csv
   *.png
   ```

3. **Document model changes**
   ```bash
   git commit -m "Increase reservoir capacity to 6M m³ for scenario 2"
   ```

## Troubleshooting

### Project Scaffolding Issues

#### 1. Invalid Project Name

**Error:**
```
ValueError: Project name 'my/project' contains invalid characters: /
```

**Solution:**
Use only alphanumeric characters, underscores, and hyphens in project names:
```python
# Good
waterlib.create_project("my_water_model")
waterlib.create_project("regional-model-2024")

# Bad
waterlib.create_project("my/project")  # Contains /
waterlib.create_project("model:v1")    # Contains :
```

**Platform-specific invalid characters:**
- Windows: `< > : " / \ | ? *`
- macOS/Linux: `/`

#### 2. Project Already Exists

**Error:**
```
FileExistsError: Project directory already exists: /home/user/my_model
```

**Solution:**
Either choose a different name or use the `overwrite` parameter:
```python
# Option 1: Use a different name
waterlib.create_project("my_model_v2")

# Option 2: Overwrite existing project
waterlib.create_project("my_model", overwrite=True)
```

**Warning:** Using `overwrite=True` will delete the existing project directory and all its contents!

#### 3. Parent Directory Not Found

**Error:**
```
FileNotFoundError: Parent directory does not exist: /nonexistent/path
```

**Solution:**
Create the parent directory first or use an existing directory:
```python
import os

# Option 1: Create parent directory first
os.makedirs("/projects/water_models", exist_ok=True)
waterlib.create_project("my_model", parent_dir="/projects/water_models")

# Option 2: Use current directory (default)
waterlib.create_project("my_model")

# Option 3: Use an existing directory
waterlib.create_project("my_model", parent_dir="./existing_folder")
```

#### 4. Permission Denied

**Error:**
```
PermissionError: Cannot create project in /protected/path: Permission denied
```

**Solution:**
- Use a directory where you have write permissions
- On Unix systems, check directory permissions: `ls -la /path/to/parent`
- Try creating in your home directory or current working directory:

```python
# Create in home directory
import os
home = os.path.expanduser("~")
waterlib.create_project("my_model", parent_dir=home)

# Create in current directory
waterlib.create_project("my_model")  # Uses current directory by default
```

#### 5. Generated Files Not Working

**Problem:** The generated Python script or YAML file doesn't work as expected.

**Solution:**
1. **Check waterlib version**: Ensure you have the latest version
   ```bash
   pip install --upgrade waterlib
   ```

2. **Verify file contents**: Open the generated files and check for corruption
   ```python
   # Test the generated model
   import waterlib
   model = waterlib.load_model("my_model/models/baseline.yaml")
   print("Model loaded successfully!")
   ```

3. **Regenerate the project**: If files are corrupted, recreate the project
   ```python
   waterlib.create_project("my_model", overwrite=True)
   ```

### Common Model Errors

#### 1. Missing Required Parameter

**Error:**
```
ConfigurationError: Component 'demand' of type 'Demand' is missing required
parameter 'population'. Required parameters for municipal mode: population, per_capita_demand_lpd
```

**Solution:**
Add the missing parameter to your YAML:
```yaml
demand:
  type: Demand
  mode: municipal
  population: 50000  # Add this
  per_capita_demand_lpd: 200
```

#### 2. Circular Dependency

**Error:**
```
CircularDependencyError: Model contains circular dependencies:
reservoir_a -> pump_b -> reservoir_c -> reservoir_a
```

**Solution:**
Add a `LaggedValue` component to break the cycle:
```yaml
lagged_value:
  type: LaggedValue
  source: reservoir_a.storage
  initial_value: 2000000

pump_b:
  type: Pump
  control_source: lagged_value  # Use lagged value instead of direct connection
```

#### 3. Date Not Found in Climate Data

**Error:**
```
KeyError: Date 2020-01-15 not found in climate data.
Available date range: 2020-01-01 to 2020-01-10
```

**Solution:**
- Check that your climate data covers the full simulation period
- Verify date formats in your CSV files
- Ensure `start_date` and `end_date` are within data range

#### 4. File Not Found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/precip.csv'
```

**Solution:**
- Check that file paths are relative to the YAML file location
- Verify the file exists: `ls data/precip.csv`
- Use forward slashes even on Windows: `data/precip.csv`

### Getting Help

1. **Check the examples**
   - Look in `examples/` directory for similar models
   - Run example scripts to verify installation

2. **Enable debug logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   model = waterlib.load_model('my_model.yaml')
   ```

3. **Validate your YAML**
   ```python
   import waterlib

   # This will show detailed error messages
   try:
       model = waterlib.load_model('my_model.yaml')
       print("Model loaded successfully!")
   except Exception as e:
       print(f"Error: {e}")
   ```

4. **Ask for help**
   - Open an issue on GitHub
   - Include your YAML file (or a minimal example)
   - Include the full error message
   - Describe what you're trying to achieve

## Next Steps

Now that you understand the basics:

1. **Explore the examples**
   - Run all examples in the `examples/` directory
   - Modify them to understand how changes affect results

2. **Build your own model**
   - Start with a simple model
   - Add complexity gradually
   - Test each addition before moving on

3. **Learn advanced features**
   - Read about feedback loops in the main README
   - Explore property-based testing
   - Contribute to the project

4. **Share your work**
   - Write about your models
   - Share interesting results
   - Contribute examples back to the project

Happy modeling!
