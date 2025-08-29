#!/bin/zsh
set -euo pipefail
DIR=$(cd -- "$(dirname -- "$0")" && pwd)

python3 -m pip install --user -r "$DIR/requirements.txt" | cat
python3 -m streamlit run "$DIR/app_streamlit.py" --server.headless=true --server.port=8501

