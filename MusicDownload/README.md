# MAESTRO.ai - Phase 1: Data Pipeline & Preprocessing

## Overview
Phase 1 implements a robust data collection and preprocessing pipeline for audio processing. This phase focuses on gathering high-quality audio data, standardizing formats, and preparing the dataset for further processing.

## Table of Contents
- [Setup](#setup)
- [Data Pipeline Architecture](#data-pipeline-architecture)
- [Features](#features)
- [Usage](#usage)
- [Quality Control](#quality-control)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)
- [Contributing](#contributing)

## Setup

### Prerequisites
```bash
# System Dependencies
brew install ffmpeg libsndfile   # macOS
# or
sudo apt-get install ffmpeg libsndfile1-dev   # Ubuntu/Debian

# Python Environment
python -m venv env
source env/bin/activate
pip install -r requirements.txt
brew install ffmpeg  # macOS

OR

sudo apt-get install ffmpeg  # Ubuntu

brew install libsndfile  # macOS

OR

sudo apt-get install libsndfile1-dev  # Ubuntu

PS: sorry we don't do windows
```

Usage
Basic Commands
To run the complete pipeline:

```
python optimized_pipeline.py --config config.json --project-dir .
```

Skipping Phases - 
The pipeline allows skipping specific phases for greater flexibility:

1. Skip Download Phase:

```
python optimized_pipeline.py --config config.json --project-dir . --skip download
```

Skip Multiple Phases:

```
python optimized_pipeline.py --config config.json --project-dir . --skip download features
```

Other Combinations:
```
# Skip only feature extraction:
python optimized_pipeline.py --config config.json --project-dir . --skip features
# Skip metadata extraction:
python optimized_pipeline.py --config config.json --project-dir . --skip metadata
# Skip features and metadata:
python optimized_pipeline.py --config config.json --project-dir . --skip features
```

mermaid
```
graph TD
    A[YouTube Source] --> B[Download Module]
    B --> C[Quality Check]
    C --> D[Metadata Extraction]
    D --> E[Format Standardization]
    E --> F[Dataset Organization]
    F --> G[Database Storage]
```
