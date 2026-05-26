"""Deprecated Streamlit entrypoint kept for backward compatibility.

Use ``streamlit run app/main.py`` as the official frontend entrypoint.
"""

from __future__ import annotations

from app.main import main as run_main


def main() -> None:
	"""Forward execution to the unified Streamlit shell entrypoint."""

	run_main()


if __name__ == "__main__":
	main()
