# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

COPY fetch_kanpo.py /fetch_kanpo.py

# 依存ライブラリ
COPY pyproject.toml /pyproject.toml
RUN uv pip install -r /pyproject.toml

CMD ["uv", "run", "fetch_kanpo.py"]