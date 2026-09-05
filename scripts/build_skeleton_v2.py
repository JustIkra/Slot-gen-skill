"""Compatibility entrypoint; implementation is owned by slot-spine-skin."""
try:
    from slotspine_tools import build_skeleton_v2 as _implementation
except ImportError as error:
    raise ImportError("Install the sibling Spine package in this environment: pip install -e ../slot-spine-skin") from error

globals().update({name: value for name, value in vars(_implementation).items() if not name.startswith("__")})

if __name__ == "__main__":
    _implementation.main()
