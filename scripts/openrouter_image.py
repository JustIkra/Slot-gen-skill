"""Compatibility CLI and Python imports for the shared OpenRouter client."""
try:
    from slotgen_provider import openrouter as _implementation
except ImportError as error:
    raise ImportError("Install slotgen-provider in this Python environment: pip install -e .") from error

globals().update({name: value for name, value in vars(_implementation).items() if not name.startswith("__")})

if __name__ == "__main__":
    _implementation.main()
