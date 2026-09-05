# Video masters

Use the slot-gen video client for coherent image-to-video masters. A video is a source
artifact; it is not automatically a production frame sequence.

    python scripts/gen_video.py --first start.png --last end.png --prompt "Locked camera; coherent plasma motion" --out .tmp_video/master.mp4 --job-file .tmp_video/job.json

The configured default remains kwaivgi/kling-v3.0-std, 5 seconds, 720p, 1:1, without audio.
Pass changes explicitly and verify supported provider options before spending. Derive anchors
from one master so geometry, framing and exposure match. Opaque subjects can use a suitable
chroma background; light should use black. Do not upload proprietary sources to public hosts.

Use --action submit to persist a task ID and return, --action resume to poll/download,
or --action download for an already ready job. The default auto submits once and waits.
To continue an existing task without the source arguments:

    python scripts/gen_video.py --action resume --job-file .tmp_video/job.json

If submission_unknown is recorded, do not submit again automatically. Reconcile the provider
task or explicitly choose a new job. Existing jobs with different inputs are refused.
Polling deadlines preserve the task record for a later resume.

Review the full clip for camera drift, contour stability, lighting coherence and actual
movement. Send the accepted master to slot-spine-skin only when frame extraction/rigging is
requested. Continuous FX should first be considered for reusable layers/mesh; any frame
sequence must pass the target game's packed-texture budget.
