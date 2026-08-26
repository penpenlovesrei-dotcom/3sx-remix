# Docs

## This fork's own

Four things this fork adds, each documented where the code is.

| | |
|---|---|
| [bgm_remix.md](bgm_remix.md) | user-supplied soundtracks, one pack per folder, chosen per stage |
| [palettes.md](palettes.md) | palette sets for the cast and the stages, and how a set is chosen in game |
| [color_edit.md](color_edit.md) | the in-game colour editor, what it writes, and the rendering traps behind it |
| [tex_remix.md](tex_remix.md) | replacing individual textures |
| [traduction_texte.md](traduction_texte.md) | translating quotes, pre-fight dialogue and endings |
| [traduction_police.md](traduction_police.md) | what the font can draw, and why the translation stops where it does |

## Upstream's

[building.md](building.md) · [config.md](config.md) · [resources.md](resources.md) ·
[statcheck.md](statcheck.md)

## What is not here

Session handoffs — the state of a piece of work, what was tried, what is still open — live outside
the repository, in `Downloads\SF3.3 music\`:

| | |
|---|---|
| `3sx-coloredit-briefing.md` | the most recent, and it **corrects the palette one** on several points |
| `3sx-palettes-briefing.md` | the palette loader and the capture tooling |
| `3sx-mod-briefing.md` | the music |
| `3sx-hd-briefing.md` | the HD artwork |

Those are dated notes for whoever picks the work up next. The files above are for whoever reads the
code. When the two disagree about how something works, the code and these files win: a briefing
records what was true the day it was written.
