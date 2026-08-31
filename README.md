<div align="center">
  <img src="images/logo_satquery.png" alt="SatQuery AI Logo" width="300"/>
  <h1>SatQuery AI: Agentic Vision-Language Assistant for Remote Sensing</h1>
  <p>An interactive, multi-modal, agentic framework for analyzing single and paired remote-sensing images through natural-language queries.</p>
</div>

---

## 🌍 Overview

**SatQuery AI** is an advanced agentic remote-sensing and geospatial intelligence system designed for the **ISRO Hackathon**. It transcends basic single-task Vision-Language Models (VLMs) by implementing an **autonomous agent pipeline**. 

Instead of applying a single generic VLM, the system interprets the user's natural language query, selects suitable remote-sensing specialist tools (Change Detection, Optical-SAR Fusion, Grounding), validates geospatial inputs, executes the workflow, and returns an **Evidence-Grounded** response.

## 🚀 Key Features (Hackathon Requirements Satisfied)

* **Multi-Image Change Analysis:** Native support for Bi-Temporal GeoTIFF pairs. The system automatically detects, localizes, and describes changes between T1 and T2 images.
* **Cross-Modal Pair Analysis:** Ingests and spatially aligns co-registered Optical/Multispectral and SAR imagery to extract complementary structural and spectral information.
* **Single-Image VQA & Grounding:** Baseline visual question answering and text-guided region bounding box grounding.
* **Agentic Orchestration:** A dynamic planner, intent parser, and tool executor that autonomously routes queries to the correct remote-sensing logic.
* **Interactive Web GUI:** A sleek, glassmorphism-styled dashboard for seamless visual interaction and analysis.
* **Remote-Sensing Adapted Models:** Integrated support for HuggingFace VLMs fine-tuned on **BigEarthNet** (e.g., `RS-llava-v1.5-7b-LoRA`).

## 🏗️ Architecture

SatQuery AI was built iteratively across 14 rigorous development phases:

- **Phases 1-4:** Geospatial Input Foundation, Agentic Orchestration, Analytical Tools, and Temporal Intelligence.
- **Phases 5-7:** Multimodal (Optical/SAR) processing, Model Abstractions, and Grounded VLM Reasoning.
- **Phases 8-10:** Benchmarking infrastructure, Evaluation Metrics (VRSBench, RSVQA, CDVQA), and Reproducibility parameters.
- **Phases 11-14:** Full-System Production Audit, Security Hardening, Frontend Web GUI Development, and Final Release Candidate Certification.

## 🛠️ Quick Start (Dockerized Deployment)

SatQuery AI is fully containerized. To spin up the backend API, Postgres database, and Redis cache:

```bash
git clone https://github.com/ainaanraza/SatQuery.git
cd SatQuery

# Build and Start the infrastructure
docker compose -f docker-compose.gpu.yml up -d
```

To run the interactive Frontend UI locally:
1. Open `satquery/frontend/index.html` in your browser.
2. The UI will automatically connect to the FastAPI backend running on port `8001`.

## 🧠 Model Integration (HuggingFace)

SatQuery AI relies on external, fine-tuned Vision-Language Models (VLMs) for semantic reasoning. We provide out-of-the-box integration for HuggingFace models.

Set your environment variables to route queries to your BigEarthNet fine-tuned model:
```bash
export SATQUERY_ENV="production"
export SATQUERY_MODEL_PROVIDER="hf_llava"
```

## 📊 Evaluation Benchmarks

The system includes built-in scripts to evaluate your fine-tuned models against public academic datasets required by the problem statement:

```bash
# Evaluate on RSVQA
python -m satquery.benchmark --dataset /path/to/rsvqa --split test

# Evaluate on CDVQA
python -m satquery.benchmark --dataset /path/to/cdvqa --split test
```

## 🔒 Security & Integrity
SatQuery enforces strict **Absolute Integrity Rules**. The `EvidenceGraph` ensures that every semantic claim outputted by the model is directly linked to deterministic geospatial coordinates or tool observations, preventing hallucinated responses.

---
*Built for the ISRO Remote Sensing AI Hackathon.*
