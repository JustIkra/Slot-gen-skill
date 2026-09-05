"""OpenRouter image-to-video CLI with persistent jobs."""
try:
    from slotgen_provider.video import run_cli
except ImportError as error:
    raise ImportError("Install slotgen-provider in this environment: pip install -e .") from error

if __name__ == "__main__":
    try:
        run_cli()
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error))
