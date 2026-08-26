# COLOR EDIT MODE

An editor for a character's colours, with the character on screen while you change them. It writes
a [palette set](palettes.md) like any other, into `pal_remix/color-edit/`, so what comes out of it
is indistinguishable from a set captured off an arcade board.

**Options → Display → COLOR EDIT → a character.**

## What is on screen

| | |
|---|---|
| Left panel | the fighter, in the palette being edited. A change shows on the next frame. |
| Right panel | the same fighter as a **mask**: black everywhere, white only where the colour under the cursor is actually painted. |
| Bottom strip | all 64 colours of the palette, cursor on one. |
| Left bars | the three channels, each in its own colour, the one being changed at full strength. |
| Right rows | the character's name and the button its colour answers to, then `COLOR` and `SAVE`. |

The mask is what a grid of swatches cannot tell you. A palette holds near neighbours and a good
deal of padding nothing draws, and moving a channel on the wrong entry looks exactly like moving it
on an unused one. An entry that is transparent in play stays transparent in the mask, so an empty
panel means "nothing draws this" rather than "nothing found".

## Controls

| | |
|---|---|
| Confirm / Cancel | walk the three levels: rows ↔ swatches ↔ channel bars |
| Lever, on the swatches | move the cursor over the 64 colours |
| Lever, on the bars | left and right pick the channel, up and down change it |
| L1 / R1 | the colour being edited, named by its button |
| L2 / R2 | step the pose |
| Lever, on `COLOR` | which set to work from: 3rd Strike, New Gen, 2nd Impact, Color Edit |
| Lever, on `SAVE` | which button's colour the file will be written to |
| Confirm, on `SAVE` | write it |

`SAVE` need not target the colour being edited: a shade worked out on one button is often wanted on
another, which is most of what an editor is for.

Changing the set rereads the entry, so unsaved changes to the row being left are lost.

## What it writes

`pal_remix/color-edit/char-NN.pal` — the whole archive entry, with the edited row put back in
place and every other row exactly as it was read. The folder is created on the first save, and the
loader picks the file up without a restart.

Two sources are needed to write that file, and neither is where you would first look:

- **`ColorRAM` holds eleven of the twenty-eight rows** — the coloris in play, the six effect
  palettes and the four the portrait uses. An entry rebuilt from it would lose the other fifteen
  coloris outright.
- **The archive buffer is released** a few lines after it is read, so `color3rd` keeps a copy of
  the game's own entry while it is still alive. `palGetPlayerSource` hands it back.

## Rendering traps

Everything here fails **silently**. They are commented where they bite, in `col_edit.c`, and
collected here because most of them cost a day each.

- **A character's multitexture is a streaming one.** Its cache is open only between
  `init_texcash_before_process` and `texture_cash_update`, both inside `Game_Task`. A sprite pushed
  from outside that window is asked for, never committed, and comes out **invisible** rather than
  wrong. That is why the preview lives in the effect move table rather than in the menu's own code.
- **Mode 17 reads the DC ghost palette** while character colours go to the CP3 one. Players cross
  that bridge through `exchange_current_colcd`; anything else calls `push_color_trans_req` by hand.
- **`exchange_current_colcd` derives a ghost slot from the work's id** when `work_id == 1`. A work
  whose id is an effect table slot then writes kilobytes past the end of `colPalBuffDC`. Use
  `work_id = 0`.
- **`my_col_code` is an offset, not an index.** The sprite path computes `(attr & 0x1FF) + colcd`,
  so a sprite reads a *run* of slots from there. To find which slot a sprite draws from, flood each
  slot of the run with its own unmistakable colour and look.
- **`my_clear_level` is a transparency, not a brightness.** 0 is opaque, 128 half.
- **Never `SDL_zero` a work fresh from `pull_effect_work`.** It is already clean, and clearing it
  takes the work out of its own linked list.
- **Release a player's assets by key type, never by group.** A player request brings in more than
  the character's own textures, and freeing only some of them gives a fatal duplicate transfer on
  the next load. `purge_player_texture` then `Purge_memory_of_kind_of_key`.
- **`IO_Result` is written by `MC_Move_Sub`**, not by reading the stick. A screen that does not
  call it sees no button at all.
- **`effect_61` bakes its string once**, one sprite per letter. A line whose text changes has to be
  torn down and built again; `effect_61_last_work` is how you name the one to take down, since
  `Menu_Suicide` kills every line sharing a `master_player`.
- **The image is anamorphic**: the window is asked for 640×480 for a 384×224 picture, so the
  vertical is stretched by about 1.29. A square drawn square comes out tall.

## Adding a menu row

`Menu_Letter_Data` and `Slide_Pos_Data_61` are indexed by the same number and must stay the same
length. An entry inserted anywhere moves every index after it — including the ones this screen and
the Custom screens name by constant — so **append past the end** and place it there. The same holds
for `Letter_Data_64` and `Slide_Pos_Data_64`, and for `EFF04_Cursor_Data` when a row needs a cursor.

When merging upstream, check every such constant against the string it is supposed to name. A row
removed upstream shifts them all by one, nothing fails to compile, and the wrong label is simply
drawn.
