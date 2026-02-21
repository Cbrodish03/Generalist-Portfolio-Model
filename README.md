# 📊 Generalist Portfolio Optimization Tool

> A stochastic portfolio optimization tool for analyzing investment decisions under uncertainty using SIPMath 2.0 simulation data.

---

## 📋 Table of Contents

- [Project Description](#-project-description)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [Usage Instructions](#-usage-instructions)
  - [Parsing a SIP File](#parsing-a-sip-file)
  - [Generating Portfolios](#generating-portfolios)
  - [Winds of Fortune](#winds-of-fortune)
  - [Exporting Results](#exporting-results)
- [Project Structure](#-project-structure)
- [Architecture Overview](#-architecture-overview)
- [Credits](#-credits)
- [License](#-license)

---

## 📖 Project Description

The **Generalist Portfolio Optimization Tool** is a desktop application for financial portfolio analysis grounded in probabilistic simulation. Rather than relying on static point estimates, it ingests SIPMath 2.0-compliant stochastic simulation files—where each investment is represented by thousands of Monte Carlo trial outcomes—and uses those distributions to construct and compare portfolios with real-world uncertainty baked in.

### Why It Was Built

Traditional portfolio tools assume deterministic inputs (e.g., a single expected return value). This leads to overconfident recommendations that ignore the full distribution of possible outcomes. The Generalist Portfolio Model was designed to address this gap by:

- Treating investment returns as **distributions**, not point estimates
- Generating **Dirichlet-distributed random portfolios** to explore the full risk/return space
- Computing the **Markowitz efficient frontier** using quadratic programming over sampled trial data
- Integrating **Winds of Fortune** — a scenario layer that adjusts trial outcomes based on correlated external market factors

### Problems Solved

| Problem | Solution |
|---|---|
| Deterministic inputs hide downside risk | Probabilistic SIPMath trials encode full return distributions |
| Single portfolio analysis is too narrow | Dirichlet sampling generates diverse portfolio combinations |
| Efficient frontier is hard to compute from raw trials | Mean/variance matrices are derived directly from trial statistics |
| Market correlations are ignored | Winds of Fortune adjusts investments by shared wind coefficients |
| Results are difficult to reproduce | Seeded RNG guarantees exact reproduction of any run |

---

## ✨ Key Features

- **SIPMath 2.0 File Parsing** — Supports standard SIP files, Winds of Fortune template files, and Winds SIP files
- **Dirichlet Random Portfolio Generation** — Constructs `n` portfolios with random asset weights that always sum to 1
- **Markowitz Efficient Frontier** — Computes variance-minimizing weights for target returns via convex quadratic programming (`cvxpy`)
- **Pareto Efficiency Evaluation** — Identifies which random portfolios are non-dominated across average return and P10 operating margin
- **Winds of Fortune Integration** — Applies wind adjustment layers to investment trial data using configurable coefficients
- **Interactive Scatter Plot** — Click any portfolio point to view its full metadata, weights, and statistics
- **Portfolio Search** — Jump directly to any portfolio by its numeric ID
- **Visualization Caching** — LRU cache prevents redundant recomputation for repeated settings
- **Seeded Randomness** — All generation is reproducible with an optional integer seed
- **CSV Export** — Export all random and efficient portfolios to a structured `.csv` file
- **Fixed Axis Scaling** — Optionally lock axis bounds for cross-run comparisons

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| UI Framework | CustomTkinter + Tkinter |
| Plotting | Matplotlib |
| Numerical Computing | NumPy |
| Optimization | CVXPY (SCS solver) |
| Data Parsing | Pandas + `python-calamine` |
| File Format | SIPMath 2.0 (`.xlsx`) |

---

## ⚙️ Installation & Setup

### Prerequisites

- Python **3.11 or higher**
- `pip` package manager

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-org/generalist-portfolio-model.git
cd generalist-portfolio-model
```

### Step 2 — Create and Activate a Virtual Environment

```bash
# Create
python -m venv .venv

# Activate (macOS / Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

**Core dependencies:**

```
numpy
pandas
python-calamine
matplotlib
cvxpy
customtkinter
```

### Step 4 — Add Your Data Files

Place SIPMath 2.0-compliant `.xlsx` files into the `/data` directory at the project root. The application scans this folder automatically on startup.

```
generalist-portfolio-model/
├── data/
│   ├── your_sip_file.xlsx
│   ├── Winds_of_Fortune_Template.xlsx
│   └── Winds_of_Fortune_SIP.xlsx
├── src/
└── ...
```

### Step 5 — Launch the Application

```bash
python src/new_ui.py
```

---

## 🚀 Usage Instructions

### Parsing a SIP File

1. Launch the application (`python src/new_ui.py`)
2. In the **File Configuration** tab, select your `.xlsx` SIP file from the dropdown menu
3. Click **"Parse File"**
4. The **File Details** tab will populate with a summary of all investments, metadata, and the first 5 trial values per asset

> ℹ️ All `.xlsx` files in the `/data` folder are automatically detected on startup.

---

### Generating Portfolios

1. With a file parsed, enter the number of desired random portfolios in the **Samples** field (1–1000)
2. Optionally enter an integer **Random Seed** for reproducible results — leave blank to generate a random seed (logged to the console)
3. Click **"Run Visualization"**
4. The **Graph** tab will display a scatter plot of:
   - 🔵 **Blue dots** — Dirichlet-random portfolios
   - 🔴 **Red stars** — Markowitz efficient frontier portfolios
   - **Red dashed line** — Efficient frontier curve
5. **Click any point** to view its full breakdown in the Portfolio Information panel (right side)
6. Use the **search box** to jump to a specific portfolio by its number (e.g., `42`)

**Axis:**
- X-axis → **Risk** (10th percentile operating margin, in dollars)
- Y-axis → **Average Return** (expected return, in dollars)

**Settings Panel (right sidebar):**

| Setting | Description |
|---|---|
| Toggle Efficient Frontier | Show/hide the frontier curve and star markers |
| Use Winds of Fortune | Switch to wind-adjusted investment data |
| Use Fixed Axis Scale | Lock axis bounds across runs |
| Visualization Cache Size | Control how many runs are cached in memory |

---

### Winds of Fortune

Winds of Fortune allows external market factors ("winds") to shift investment returns based on pre-configured coefficients.

**Setup:**

1. Navigate to the **Winds of Fortune** tab in the control panel
2. Select your **Template File** (defines investment-to-wind coefficient mappings)
3. Select your **Winds SIP File** (provides trial values for each wind)
4. Click **"Load Winds of Fortune Files"**
5. Enable **"Use Winds of Fortune"** in the Settings panel before running a visualization

**How It Works:**

For each trial `t`:
```
adjusted_return[t] = base_return[t] + (wind_coefficient × wind_value[t])
```

Winds are applied per-investment based on the coefficients defined in the template file.

---

### Exporting Results

After generating portfolios, click **"Export Portfolio Info to CSV"** in the Portfolio Information panel.

You will be prompted for a filename. The exported `.csv` will be saved to the `/data` directory and includes:

| Column | Description |
|---|---|
| Portfolio Type | `Random` or `Efficient` |
| Index | 1-based display ID |
| Average Return | Mean return in dollars |
| Variance | Portfolio variance |
| Standard Deviation | Square root of variance |
| Weight 1…N | Asset allocation percentages |

---

## 📁 Project Structure

```
generalist-portfolio-model/
│
├── data/                        # SIPMath .xlsx input files (user-provided)
│
├── src/
│   ├── new_ui.py                # Main application entry point (CustomTkinter UI)
│   ├── SIP_UI.py                # Legacy Tkinter UI (deprecated)
│   ├── parser.py                # SIPParser — handles all .xlsx file parsing
│   ├── portfolio.py             # Portfolio construction (custom, random, efficient)
│   ├── sample_portfolios.py     # Dirichlet random portfolio generator + Pareto eval
│   ├── variance_calcs.py        # Mean/variance matrix construction + frontier coefficients
│   └── visualization.py        # Matplotlib plotting, tooltips, formatting, export
│
└── README.md
```

---

## 🏗 Architecture Overview

```
SIPParser (parser.py)
    │
    ├── parse_standard_sip()      → investment trial data
    ├── parse_winds_template()    → wind coefficient mappings
    └── apply_winds()             → adjusted trial data
             │
             ▼
    Portfolio (portfolio.py)
    ├── rand_weights()            → Dirichlet-sampled weights
    ├── eff_weights()             → CVXPY quadratic program
    └── construct_port()          → computes mean, variance, P10
             │
             ├───────────────────────────┐
             ▼                           ▼
    RandomPortfolios              variance_calcs.py
    (sample_portfolios.py)        ├── create_matrices()
    ├── generate_sample()         └── compute_coeffs()
    └── pareto_eval()
             │
             ▼
    visualization.py
    ├── visualize_portfolios()    → fig, TooltipManager, portfolios
    ├── plot_frontier()           → efficient frontier points
    ├── TooltipManager            → hover + click interaction
    └── export_portfolios_to_csv()
             │
             ▼
    new_ui.py (App)
    ├── parse_selected_file()
    ├── run_visualization()       → cache lookup → generate → embed figure
    ├── load_wind_files()
    └── export_current_portfolios()
```

---

## 🙏 Credits

Developed as part of a financial decision-support research initiative.

- **SIPMath Standard** — Developed by [ProbabilityManagement.org] (http://www.sipmath.org/) — the SIPMath 2.0 specification defines the stochastic interchange format used throughout this project
- **CVXPY** — Convex optimization library used for Markowitz efficient frontier computation: [cvxpy.org](https://www.cvxpy.org/)
- **CustomTkinter** — Modern Tkinter UI framework by Tom Schimansky: [github.com/TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **python-calamine** — High-performance Excel parsing backend used by Pandas for `.xlsx` ingestion

---

## 📄 License

This project is distributed under the **MIT License**.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<div align="center">
  <sub>Built with Python · Powered by probabilistic simulation · Designed for decision-making under uncertainty</sub>
</div>
