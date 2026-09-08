# Third-party notices

## video-shotcraft

- Upstream: https://github.com/Vincentwei1021/video-shotcraft
- Copyright 2026 Wei Yihao
- License: Apache-2.0, preserved at `vendor/video-shotcraft/LICENSE`
- Pinned commit: `5f047c7cfe10d6616fe59160a750fcfaea510b2e`
- Files are preserved without text/code modification; Vox-specific integration lives outside the vendor directory.
- Third-party MP3 files, MP4 previews, Git history, CI and runtime caches are excluded. Audio attribution records remain but do not imply audio redistribution permission. See `references/shotcraft-integration.md` for dependency and asset preparation limits.

## vox-director

This repository vendors portions of `vox-director`:

- Upstream: https://github.com/Alisa0808/vox-director
- Copyright: Copyright (c) 2026 Alisa Qian
- License: MIT
- Vendored path: `vendor/vox-director/`

The upstream license is preserved at `vendor/vox-director/LICENSE`.

The vendored code supplies Director workflow guidance, prompts, examples and helper scripts. The outer `vox-editing-style` Skill adds the talking-head content-audit, execution-outline, layered-scene, Remotion review, caption, BGM/SFX and QC contracts.

Large upstream MP4 showcase files and the duplicate packaged `.skill` archive are intentionally not redistributed in this beta repository. Thumbnail images and links remain for attribution and reference. View the original showcases in the upstream repository.
