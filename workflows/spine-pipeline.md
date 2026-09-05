# Handoff to the Spine owner

Spine authoring is owned by slot-spine-skin. Do not follow a second implementation here.
slot-gen produces source art, separated PNGs and video masters with a stable canvas.

Hand over accepted parts, reference image, pivots/layout when known and the intended motion.
Use slot-spine-skin for positioning, bone hierarchy, JSON, animation presets, atlas packaging
and installed-runtime preview. Its runtime validator and atlas-budget checker are the gate.

Old Python command paths in scripts/ remain compatibility entrypoints to the installed
slotspine-tools package. Install the sibling repository into the same environment if an
existing caller still uses these paths. There is no second maintained skeleton generator.
