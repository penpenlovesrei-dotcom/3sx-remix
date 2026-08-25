# Remix BGM packs

3SX can play user-supplied soundtracks, selectable from **Options → Sound → BGM Type** alongside
the game's own `Arrange` and `Original`. Each pack adds a value to that row, and the row's order
and labels are yours to set.

A pack overrides tracks one by one. Anything it doesn't cover keeps playing the arranged track,
so a pack may hold a single stage theme or a whole soundtrack.

## Installing a pack

One folder per pack under `bgm_remix`, in your [resources](resources.md) folder:

```
resources/
├── SF33RD.AFS
└── bgm_remix/
    ├── menu.txt                 (optional, sets the row's order and labels)
    ├── new-generation/
    │   ├── remix.txt
    │   └── theme_alex.adx
    └── 2nd-impact/
        ├── remix.txt
        └── ...
```

Restart the game. Packs are read once at startup, so adding one, renaming one or editing a
manifest needs a restart to take effect.

Up to 8 packs can be installed at once.

## The manifest

Each pack's `remix.txt` names it and maps BGM codes to files:

```
!name New Generation

# bgm code | file name | sound test label
1  | theme_alex.adx | 1. Alex Stage -NEW GENERATION-
4  | theme_necro.adx
53 | player_select.adx | 53. Player Select -NG-
```

- **`!name`** — what the pack shows on the `BGM Type` row. Up to **9 characters** keeps the
  menu's own lettering; up to **16** is allowed, but such a value is drawn with the smaller
  lettering to fit the room the row has. A `~` in the name flips between the two mid-text, so
  `Original/~PS2` keeps the suffix full size, and `/` inserts a half-width space.
- **`!structure arcade`** — declare that the pack follows the arcade soundtrack's layout: two
  per-round mixes per stage instead of three. The sound test then skips the third-mix codes the
  arcade never had rather than listing them as duplicates, the per-round rotation comes from the
  arcade selector, and codes the pack leaves out fall back to arcade tracks rather than arranged
  ones. Omit it, or write `!structure console`, for the three-mix layout.
- **`!volume <dB>`** — correct the pack's level, e.g. `!volume -4.6`. The game sets each track's
  volume from tables calibrated for how loudly Capcom mastered that soundtrack, so a pack
  mastered to a different reference plays louder or quieter than the rest of the game for that
  reason alone. Only the pack's own tracks are corrected; codes it doesn't cover keep the level
  the game intends. A comma is accepted as the decimal mark.
- **bgm code** — 1 to 67. See the table below.
- **file name** — relative to the pack folder.
- **sound test label** — optional. Without it the arranged label is used. Printable ASCII only,
  cut to 44 characters.
- Lines starting with `#` are comments. Blank lines are ignored.

[`remix.template.txt`](remix.template.txt) lists all 67 codes ready to uncomment.

Entries pointing at a missing or unsupported file are skipped with a warning in the log, and the
arranged track plays instead. A pack whose entries all fail is hidden rather than half-working.

## Soundtracks with no per-round mixes

3rd Strike plays a different mix of a stage theme on each round: codes 1/2/3 are mix 1/2/3 of the
first stage, 4/5/6 the second, and so on up to code 48.

A soundtrack that has no such variation only needs the **mix 1** line of each stage. The other two
rounds fall back to it, and because all three rounds then resolve to the same file, the track
**plays straight through the round transitions** rather than restarting — the game's own volume
fade still lands on it. So a one-track-per-stage pack is 16 lines, not 48:

```
!name New Generation

1  | theme_alex.adx
4  | theme_necro.adx
7  | theme_hugo.adx
```

Override all three codes of a stage when you do want a different track per round.

## The BGM Type row

Without `menu.txt` the row reads `Arrange`, `Original`, then the packs in folder order.

To choose the order and the labels, add `bgm_remix/menu.txt` — one entry per line, left to right:

```
original = Original PS2
original-cps3
arrange = Arranged
online-edition
new-generation
2nd-impact
```

- `arrange`, `original` and `random` are built in; any other name is a **pack folder**.
- `= Name` relabels an entry, which is how the stock ones get renamed.
- Anything you leave out stays reachable, placed after the entries you listed.
- A pack with no usable track never appears, listed or not.

`random` isn't a soundtrack of its own. Picking it draws one of the others **once per fight**, so
a fight's rounds keep a single soundtrack and its per-round mixes stay coherent — the game still
asks for the track it intended, only the rendition varies. The draw avoids repeating the previous
one, and uses its own random generator so the game's stays untouched: that one drives gameplay,
and the rollback netcode replays it.

Saves store the soundtrack, not its position on the row, so reordering later never repoints a
saved setting at a different one. A setting whose pack was removed falls back to the first entry.

## Preparing the audio

Tracks must be **ADX**, standard encoding, 4-bit, mono or stereo. Any sample rate works.

Encode with a CRI ADX encoder (`adxencd` and similar tools accept WAV input):

```bash
adxencd input.wav output.adx -lps<loop start sample> -lpe<loop end sample>
```

Looping is driven entirely by the loop points in the ADX header. A track encoded without them
plays once and stops — fine for a jingle, wrong for a stage theme. Build stage loops to stand on
their own, since a pack track isn't cut into the bar-aligned segments the arranged themes use.

## BGM codes

| Code | Track |
|---|---|
| 1–3 | Alex & Ken Stage — JAZZY NYC '99, mix 1/2/3 |
| 4–6 | Necro & Twelve Stage — SNOWLAND |
| 7–9 | Hugo Stage — THE CIRCUIT |
| 10–12 | Chun-Li Stage — CHINA VOX |
| 13–15 | Ryu Stage — KOBU |
| 16–18 | Ibuki Stage — TWILIGHT |
| 19–21 | Makoto Stage — SPUNKY |
| 22–24 | Akuma Stage — KILLING MOON |
| 25–27 | Elena Stage — BEATS IN MY HEAD |
| 28–30 | Sean & Oro Stage — THE LONGSHOREMAN |
| 31–33 | Dudley Stage — YOU BLOW MY MIND |
| 34–36 | Yun & Yang Stage — CROWDED STREET |
| 37–39 | Remy Stage — THE BEEP |
| 40–42 | The Theme Of Q |
| 43–45 | Urien Stage — CRAZY CHILI DOG |
| 46–48 | Gill Stage — PSYCH OUT |
| 49 | Ending 1 |
| 50 | Ending 2 |
| 51 | Just Before The Battle |
| 52 | Opening Demo |
| 53 | Player Select (arcade) |
| 54 | Final Results |
| 55 | Stage Results |
| 56 | Judgement |
| 57 | Stage Select & Score Ranking |
| 58 | Continue |
| 59 | We Await Your Return, Warrior! |
| 60 | Gill Appears! |
| 61 | Bonus Game 1 |
| 62 | Bonus Game 2 |
| 63 | Staff Roll — Moving On |
| 64 | Staff Roll — THIRD STRIKE REMIX |
| 65 | Menu — THIRD STRIKE |
| 66 | Player Select (versus) |
| 67 | Capcom Logo |
