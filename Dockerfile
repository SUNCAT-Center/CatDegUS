FROM python:3.13.5-slim-bookworm

WORKDIR /app

COPY requirements.txt .
COPY setup.py .

COPY LICENSE .
COPY README.md .

RUN mkdir imgs
RUN mkdir catdegus
RUN mkdir catdegus/active_learning
RUN mkdir catdegus/visualization

COPY catdegus/active_learning/acquisition.py catdegus/active_learning/
COPY catdegus/active_learning/functions.py catdegus/active_learning/
COPY catdegus/active_learning/gaussian_process.py catdegus/active_learning/
COPY catdegus/active_learning/__init__.py catdegus/active_learning/

COPY catdegus/visualization/plot.py catdegus/visualization/
COPY catdegus/visualization/__init__.py catdegus/visualization/

COPY catdegus/__init__.py catdegus/

RUN pip install -r requirements.txt
RUN pip install .

COPY tests/example.py .
COPY tests/example_agent.py .
COPY tests/s3fileHandler.py .
COPY tests/20250228_sheet_for_ML_unique.xlsx .