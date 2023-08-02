#!/usr/bin/env bash

curl -sSL https://install.python-poetry.org | python3 -

export PATH="$HOME/.local/bin:$PATH"
echo "export PATH=\"$HOME/.local/bin:$PATH\"" >> ~/.bashrc

poetry install