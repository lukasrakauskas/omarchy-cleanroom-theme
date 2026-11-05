# Cleanroom on Omarchy 4.5

## Intent and scope
Prioritize Neovim: use GitHub Light as the reference for Omarchy's generated Aether theme. Check other terminal applications afterwards. Preserve the existing set of GitHub Light colors, white canvas, blue desktop accent (`#005cc5`), and yellow Visual selection (`#fed442`). The user approved this palette-first approach. Exact equivalence with the GitHub plugin is not required.

## Approaches
- Selected: tune `colors.toml` for the standard Omarchy 4.5 Aether generator. No local Neovim configuration or executable theme hooks are needed.
- Not selected: load `projekt0n/github-nvim-theme` through a local plugin override. More exact, but bypasses the requested palette-first approach.
- Not selected: override Aether highlight groups. This would separate shared syntax roles, but requires local executable configuration.

## Implementation decisions
Palette keys describe Aether inputs, not necessarily literal color names. Prioritize purple functions, red keywords, dark-blue strings, blue numbers/constants and active controls, black text, and muted gray comments. Keep `accent` blue and `selection` yellow. Document shared-role compromises rather than claiming exact GitHub highlighting. Keep classic GitHub Light hex values already in Cleanroom, rather than importing the newer upstream theme's entire palette.

Use the generated Neovim configuration instead of shipping a plugin spec that Omarchy discards from Git-installed themes. Remove the redundant Ghostty built-in-theme override and let Omarchy generate terminal colors. Keep the explicit btop palette so syntax-driven semantic assignments do not degrade its functional colors. Review generated data-only app themes for usable accents and contrast; make narrowly scoped overrides only if required.

## Yellow highlighting
Aether's Visual/VisualNOS background uses `selection`, so yellow selections are supported without overrides. Normal search is derived from `blue`; active search uses `orange`. Making every search match yellow independently is outside this palette-only repair. Do not silently recolor syntax to force yellow search.

## Safety and verification
Never edit `/usr/share/omarchy`. Test generation in a temporary HOME, using the installed Omarchy 4.5 scripts. Load generated Aether in isolated headless Neovim and inspect resolved highlight colors. Reapply Cleanroom only after tests pass. Do not reset unrelated user configuration or commit changes without a request.
