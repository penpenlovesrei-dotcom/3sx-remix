#ifndef COL_EDIT_H
#define COL_EDIT_H

#include "structs.h"
#include "types.h"

#include <stdbool.h>

/// @file col_edit.h
/// The fighter preview behind COLOR EDIT MODE.
///
/// The editor is worthless without something to look at: a palette judged on swatches alone is
/// judged blind, which is the one thing the whole palette effort has had to work around. So the
/// screen brings up a real fighter, drawn from the character's own texture group with the palette
/// sitting live in `ColorRAM`. Writing a colour there shows up on the next frame.
///
/// Loading goes through `Push_LDREQ_Queue_Player`, the same request the character select screen
/// uses, which is what makes this affordable: it pulls the texture group, the animation tables and
/// the palette in one go, and the palette it pulls already passes through the `pal_remix`
/// override. The preview therefore shows whatever set the character is currently wearing, with no
/// second code path to keep in step.

/// @brief Ask for a character's assets. Asynchronous — poll ColEdit_Ready before drawing.
///
/// Only one character is held at a time; asking for another drops the one before it.
/// @param character Engine character number, as `constants.h` numbers them.
void ColEdit_Load(s16 character);

/// Whether the pending request has landed and the fighter can be drawn.
bool ColEdit_Ready(void);

/// @brief Keep the preview alive, once per frame, for as long as the screen is up.
///
/// Silently does nothing until the load lands, so the caller can call it unconditionally. This
/// does not itself draw: the drawing is done by ColEdit_Move, below.
void ColEdit_Draw(void);

/// @brief Draws a fighter. Slot 28 of the effect move table, which was a dummy.
///
/// Two works share this entry — the one being edited and the untouched reference beside him — and
/// they are told apart by pointer, not by a field, because every field that could carry the
/// distinction is already spoken for by the sprite path.
///
/// The sprite cannot be pushed from the menu task, which is where the screen's own code runs. A
/// character's multitexture is one of the streaming ones — `mts_base[3].mode` carries 0x2000 — so
/// its patterns go through a cache that is opened by `init_texcash_before_process` and closed by
/// `texture_cash_update`, both inside `Game_Task`. Pushed from outside that window the pattern is
/// asked for and never committed, and the sprite comes out invisible rather than wrong, which is
/// what made this worth a comment. Living in the effect table puts the push inside the window,
/// because `Basic_Sub` runs the effect lists from within `Game_Task`.
void ColEdit_Move(WORK* wk);

/// Give back everything held and clear the character's texture group.
void ColEdit_Unload(void);

/// @name The swatches
///
/// The sixty-four colours of the body palette — the one the colour button picks, and the only one
/// worth editing first — drawn as a grid with a cursor on one of them.
///
/// Eight by eight rather than the single strip the reference screen uses. That screen has sixteen
/// colours to show and room to lay them in a line; sixty-four across this one would leave each
/// swatch five pixels wide, too small to judge a shade by, which is the only reason to draw them
/// at all. The grid keeps every colour visible at once and gives the lever two axes to move on.
/// @{
/// Position in the palette, 0 to 63.
s16 ColEdit_Cursor(void);
void ColEdit_MoveCursor(s16 dx, s16 dy);
/// The colour under the cursor, as it sits in ColorRAM.
u16 ColEdit_Color(void);
/// @}

/// @name The palette the character arrived in
///
/// Taken once, the frame the load lands, before anything can have been changed. Three things want
/// it and none of them can be answered without it: the right-hand panel, which stands the
/// untouched fighter next to the edited one; DEFAULT COLOR, which puts a colour or the whole
/// palette back; and SAVE, which has to know what actually changed before it writes a set out.
///
/// It is kept twice — as a plain array to compare against, and mirrored into player two's
/// ColorRAM slots, which no menu has a fighter in, so that the reference fighter has a live
/// palette of his own to draw from.
/// @{
/// The colour under the cursor as the character arrived in it.
u16 ColEdit_OriginalColor(void);
/// Whether any of the sixty-four differ from what was loaded.
bool ColEdit_Modified(void);
/// Put the colour under the cursor back to what it was loaded as.
void ColEdit_RevertColor(void);
/// Put all sixty-four back.
void ColEdit_RevertAll(void);
/// @}

/// @brief A private copy of the menu palette, so one sprite can be recoloured on its own.
///
/// Every menu element — cursor, labels, banners, value columns, the page indicator — draws with
/// colour code 0x1AC. Editing that palette recolours all of them at once, which is never what is
/// wanted when the complaint is about one sprite's outline against one screen's background.
///
/// A work's colour code is its own field, though, so the way out is a second palette rather than a
/// second sprite: copy the menu's, change what needs changing, and point the one sprite at the
/// copy. Cheap, and it leaves the archive alone — a new sprite would mean new CG inside SF33RD.AFS.
///
/// @return The ColorRAM slot holding the copy, to be assigned to a work's `my_col_code`.
s16 ColEdit_MenuPaletteVariant(void);

/// @name Editing a colour
///
/// Three channels of five bits, drawn as bars rather than numbers: a bar's length is its value, so
/// it needs no charset, and the menus have no way to draw a number that changes without rebuilding
/// the effect behind it. Numbers can come later.
///
/// A change lands in ColorRAM, which the ghost palette copy already mirrors every frame, so the
/// fighter standing beside the grid takes the new colour on the very next one. That is the whole
/// point of having put him there.
/// @{
#define COL_EDIT_CHANNELS 3
/// Whether the lever is driving the channels rather than the grid
bool ColEdit_Editing(void);
void ColEdit_BeginEdit(void);
void ColEdit_EndEdit(void);
/// Step between R, G and B.
void ColEdit_SelectChannel(s16 delta);
/// Change the selected channel, clamped to 0-31 rather than wrapped: a colour dragged to an end
/// should stay there while the lever is held, not jump to the other extreme.
void ColEdit_Adjust(s16 delta);
/// @}

/// @name The pose
///
/// One pose, held still: an editor wants a stable image to judge against. A pattern is one whole
/// sprite — the trans table expands it into its pieces — and for most of the cast the second of
/// their group is the neutral stance, but not all, so the offset is a table.
///
/// Which pattern reads as a good stance cannot be worked out from the data, only looked at, and
/// nothing in the build can look. So the pose can still be stepped, on the shoulder buttons, and
/// every step is logged: that is how the table gets filled for a character whose default is wrong.
/// @{
s16 ColEdit_Pose(void);
void ColEdit_StepPose(s16 delta);
/// @}

#endif
