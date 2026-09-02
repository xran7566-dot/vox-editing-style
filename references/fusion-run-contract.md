# Fusion Run Contract

`fusion-run.json` is the operational boundary between upstream Director and one talking-head project.

## Input

The bootstrap command reads a JSON file with:

```json
{
  "project_name": "ai-matchmaking-15s",
  "source_audit": "/absolute/path/source-audit.json",
  "aspect": "9:16",
  "duration_seconds": 15,
  "source_video": "/absolute/path/source.mp4",
  "srt": "/absolute/path/captions.srt",
  "remotion_source": "/absolute/path/to/director-derived-remotion-project",
  "composition": "HybridVideo15s",
  "music": {"mode": "local_track", "path": "/absolute/path/to/generated-bgm.wav"},
  "semantic_units": [
    {
      "id": "hook",
      "time": [0, 3.77],
      "takeaway": "AI can genuinely help",
      "visual_proposition": "search and match",
      "director_brief": {
        "relationship_to_make_visible": "search can turn scattered possibilities into a decision path",
        "must_preserve": ["original voice", "creator persona"],
        "must_avoid": ["face occlusion", "single-template layout"]
      },
      "persona_brief": {"purpose": "creator memory", "allowed_forms": ["full_frame", "dynamic_cutout", "round_window", "square_window", "rectangle_window"]}
    }
  ],
  "references": [
    {"id": "open-range-map", "path": "/absolute/path/map.png", "scope": "scene_solution", "applies_to": ["open-range"]}
  ]
}
```

## Guarantees

- New v2 runs require a user-approved `vox-source-audit/v1` file. Its local artifact hashes, creator identity, semantic units, blocking issues, and review script are validated before the fusion manifest is created.
- New v2 runs must explicitly set `music`: default to a local instrumental track; use `disabled` only for an explicit user opt-out.
- Existing v1 manifests remain readable for regression and repair work, but every newly created run uses `vox-talking-head-fusion/v2`.
- Do not edit `vendor/vox-director/`.
- Record exact source paths and active rules.
- Reject missing source video, missing local Remotion project, invalid aspect, overlapping semantic units, unknown reference scope, duplicated persona in a unit, or unscoped reference.
- Make the route explicit: original audio, local Remotion, no Atlas visual generation/TTS/image-to-video/cloud assembly.
- New productions default to a separately saved local instrumental track; use `{"mode":"disabled"}` only when the user explicitly opts out. Permit Director's music model only as a separately saved, user-approved instrumental preview. It never runs the Director narration stage.
- Require each semantic unit to record a persona decision without forcing a person into the opening or any other fixed timestamp.
- Require delivered approval keyframes to be extracted from the actual Remotion composition; isolated generated posters are input assets, not review frames.
- Require a semantic Director brief for every unit; it states what viewers must understand and what must be protected/avoided, without choosing the palette, layout, component set, metaphor, or presenter form for Director.

## Limits

The manifest is not a generated video and not an artistic approval. Keyframes still require user approval; motion begins only after that gate.
