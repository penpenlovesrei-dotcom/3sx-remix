#ifndef VIDEO_CANVAS_H
#define VIDEO_CANVAS_H

/// @name The screen the game draws for
/// Every position the game hands a backend is expressed in this space, and the backends divide by
/// these to reach clip space, so this is a coordinate system rather than a buffer size. Menu
/// layouts, clipping tests and the scanline filter all count in it too.
/// @{
#define CANVAS_BASE_WIDTH 384
#define CANVAS_BASE_HEIGHT 224
/// @}

/// Largest multiple offered. 8x is 3072x1792, past what any asset can fill.
#define CANVAS_SCALE_MAX 8

/// @brief How many canvas pixels the game's own pixels are rendered into, per side.
///
/// Read from `render-scale` once, on the first call, and clamped to something a GPU will accept.
int Canvas_Scale(void);

/// @name Size of the surface the frame is rendered into, before it is scaled to the window.
/// @{
int Canvas_Width(void);
int Canvas_Height(void);
/// @}

#endif
