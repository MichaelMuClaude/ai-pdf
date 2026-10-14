# Contributing to ai-pdf

Humans and AI agents are both welcome. The detailed rules for agents are in [AGENTS.md](AGENTS.md).

- Never overwrite an input file, and require `--force` to replace an output.
- Keep JSON output and error messages stable.
- Add a test for each change. Build any PDF in the test itself; do not commit real documents.

```bash
sudo apt install qpdf
python3 -m venv ~/.venvs/ai-pdf-dev
~/.venvs/ai-pdf-dev/bin/pip install -e ".[dev]"
~/.venvs/ai-pdf-dev/bin/python -m pytest -q
```

Describe what changed, why, and which tests you ran. If an AI agent helped, say so and name the tool and model.

By contributing, you agree that your contribution is released under the MIT licence in [LICENSE](LICENSE).
