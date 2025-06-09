# Generalist-Portfolio-Model
The full specification list can be found at: https://docs.google.com/document/d/1dT3NEwn5vcZ1M1NkKXeMAkLUfadyKZlm

Developed in Python

# Overview
Web-based application that enables users to analyze and visualize business investment portfolios using stochastic simulation data in the SIPmath 2.0 format. Supports both .csv and .xlsx (Excel) files.

Key Features:
1. Automatically generates a diverse set of random portfolio combinations using Dirichlet-distributed weights to ensure that the weights sum to 1
2. Support inclusion/exclusion of assets using binary masks for discrete subset sampling
3. Filtering of investment-based constraints (expected revenue, margins, etc.)
4. Portfolio-specific calculations (mean operating margin, percentile operating margin, etc.)
5. Visualizations on a 2D scatterplot
6. User-friendly UI system, detailed below
7. Support Investment Teathering with different customizable dependency rules
8. Winds of Fortune integration to simulate real-world probable scenarios

# User Interface (UI)
Portfolio Analysis Screen
1. From uploaded SIPmath 2.0 file, set filters, select desired percentile, toggle Winds of Fortune, and display efficient frontier chart with option to export

Winds of Fortune Management Screen
1. From uploaded SIPmath 2.0 file, view each investment as row and each Wind of Fortune as column
2. Allow user to assign impact weight to each investment (-100% to 100%)
3. Save/validate controls before applying weights

Investment Teather Editor
1. A dedicated screen or modal for setting up coupling rules between investments
2. Display all investments with fields to define tethered relationships
3. Allow entry of expressions like "Investment B = Investment A × 0.5"
4. Show real-time validation and conflict resolution for rule logic
