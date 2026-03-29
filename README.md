# 🚀 PDPC – Profile Dataset Processing Client

AI-powered performance dataset analyzer for Unreal Engine profiling workflows.

---

## 📌 Overview

**PDPC (Profile Dataset Processing Client)** is a tool designed to analyze Unreal Engine performance datasets (CSV profiling data) using **locally hosted Large Language Models (LLMs)**.

It converts raw profiling data into **structured insights**, helping developers quickly identify performance bottlenecks, understand root causes, and apply fixes efficiently.

---

## ✨ Features

- 📊 **CSV Dataset Analysis**
  - Supports Unreal Engine profiling exports
  - Handles large datasets efficiently

- 🧠 **AI-Powered Insights**
  - Uses locally hosted LLMs (privacy-friendly)
  - Generates detailed analysis reports

- 📈 **Statistics Generation**
  - Frame time analysis
  - CPU/GPU breakdown
  - Bottleneck detection

- ⚠️ **Issue Detection**
  - Detects spikes and anomalies
  - Highlights performance issues

- 🔍 **Root Cause Analysis**
  - Explains *why* issues occur
  - Connects metrics to real-world problems

- 🛠️ **Suggested Fixes**
  - Actionable optimization tips
  - Unreal Engine–focused recommendations

- 🎨 **Structured HTML Reports**
  - Organized output
  - Easy-to-read analysis sections

---

## 🧩 Unreal Engine Plugin

PDPC includes an **Unreal Editor Toolbar Plugin**.

### 🔘 Features inside Unreal:
- **Start Capture**
  - Begins CSV profiling capture

- **Stop & Launch PDPC**
  - Stops capture
  - Automatically launches PDPClient

---

## 🛠️ Tech Stack

- Python
- Pandas
- Matplotlib
- Tkinter
- Local LLM API (Ollama)

---


## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sayoojjs/Profile_Data_Processor.git
```
### 2. Unreal Plugin Setup
Copy the plugin folder into:
```
YourProject/Plugins/
```
Open Unreal Engine
```
Go to Edit → Plugins
Enable PDPClient
```
Restart the editor

### 3. Python Setup

Install required dependencies:
```
pip install pandas matplotlib tkhtmlview requests
```
### 4. Setup Local LLM

- Ollama

Make sure your local model server is running.

## ▶️ Usage

### From Unreal Engine:

- Go to the menubar and click Profile Data Processor
- Click Start Capture
- Run your scene/game
- Click Stop & Launch PDPC


##From Python (Standalone):
```
python PDPC.py
```
- Select your CSV file
- Run analysis
- View generated HTML report
