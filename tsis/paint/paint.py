import pygame
import sys
import math
from datetime import datetime

from tools import (
    ToolButton, draw_toolbar, to_canvas,
    flood_fill,
    screen, clock, canvas, font,
    SCREEN_W, SCREEN_H, TOOLBAR_H,
    BG_CANVAS, BG_TOOLBAR, BORDER_CLR,
    PALETTE,
    TOOL_PEN, TOOL_LINE, TOOL_RECT, TOOL_CIRCLE, TOOL_ERASER,
    TOOL_FILL, TOOL_TEXT,
    TOOL_SQUARE, TOOL_RTRIANGLE, TOOL_ETRIANGLE, TOOL_RHOMBUS,
    plus_rect, minus_rect, clear_rect,
    size_btns,
)


def main():
    tool_buttons = [
        ToolButton( 10,  8, 58, 22, "✏ Pen",     TOOL_PEN),
        ToolButton( 72,  8, 58, 22, "╱ Line",    TOOL_LINE),
        ToolButton(134,  8, 60, 22, "▭ Rect",    TOOL_RECT),
        ToolButton(198,  8, 64, 22, "○ Circle",  TOOL_CIRCLE),
        ToolButton(266,  8, 62, 22, "⌫ Erase",   TOOL_ERASER),
        ToolButton(332,  8, 50, 22, "🪣 Fill",   TOOL_FILL),
        ToolButton(386,  8, 48, 22, "T Text",    TOOL_TEXT),
        # row 2
        ToolButton( 10, 34, 58, 22, "□ Sqr",     TOOL_SQUARE),
        ToolButton( 72, 34, 68, 22, "△ RTri",    TOOL_RTRIANGLE),
        ToolButton(144, 34, 68, 22, "△ ETri",    TOOL_ETRIANGLE),
        ToolButton(216, 34, 70, 22, "◇ Rhomb",   TOOL_RHOMBUS),
    ]

    palette_rects = []
    for i in range(len(PALETTE)):
        rx = 460 + (i % 9) * 22
        ry = 5  + (i // 9) * 22
        palette_rects.append(pygame.Rect(rx, ry, 20, 20))

    cur_tool  = TOOL_PEN
    cur_color = (0, 0, 0)
    cur_size  = 5          # medium default
    drawing   = False
    start_pos = None
    preview   = None

    # Text tool state
    text_active   = False
    text_pos      = None
    text_buffer   = ""

    while True:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard ──────────────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                # Ctrl+S — save
                mods = pygame.key.get_mods()
                if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fname = f"canvas_{ts}.png"
                    pygame.image.save(canvas, fname)
                    print(f"Saved: {fname}")
                    continue

                # Brush size shortcuts
                if event.key == pygame.K_1:
                    cur_size = 2
                elif event.key == pygame.K_2:
                    cur_size = 5
                elif event.key == pygame.K_3:
                    cur_size = 10

                # Text tool keyboard input
                if cur_tool == TOOL_TEXT and text_active:
                    if event.key == pygame.K_RETURN:
                        # Render text permanently onto canvas
                        if text_buffer:
                            txt_surf = font.render(text_buffer, True, cur_color)
                            canvas.blit(txt_surf, text_pos)
                        text_active  = False
                        text_buffer  = ""
                        text_pos     = None
                    elif event.key == pygame.K_ESCAPE:
                        text_active  = False
                        text_buffer  = ""
                        text_pos     = None
                    elif event.key == pygame.K_BACKSPACE:
                        text_buffer = text_buffer[:-1]
                    else:
                        if event.unicode and event.unicode.isprintable():
                            text_buffer += event.unicode

            # ── Mouse wheel — size ────────────────────────────────────────
            if event.type == pygame.MOUSEWHEEL:
                cur_size = max(1, min(50, cur_size + event.y))

            # ── Mouse button down ─────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos

                if y < TOOLBAR_H:
                    # Tool buttons
                    for btn in tool_buttons:
                        if btn.is_clicked((x, y)):
                            cur_tool = btn.tool_id
                            text_active = False
                            text_buffer = ""

                    # Palette
                    for idx, rect in enumerate(palette_rects):
                        if rect.collidepoint(x, y):
                            cur_color = PALETTE[idx]

                    # Size buttons
                    for sz, rect in size_btns:
                        if rect.collidepoint(x, y):
                            cur_size = sz

                    # +/- size
                    if plus_rect.collidepoint(x, y):
                        cur_size = min(50, cur_size + 1)
                    elif minus_rect.collidepoint(x, y):
                        cur_size = max(1, cur_size - 1)
                    elif clear_rect.collidepoint(x, y):
                        canvas.fill(BG_CANVAS)
                        text_active = False

                else:
                    # Canvas click
                    cx, cy = to_canvas(x, y)

                    if cur_tool == TOOL_FILL:
                        flood_fill(canvas, (cx, cy), cur_color)

                    elif cur_tool == TOOL_TEXT:
                        text_active = True
                        text_pos    = (cx, cy)
                        text_buffer = ""

                    else:
                        drawing   = True
                        start_pos = (cx, cy)
                        if cur_tool in (TOOL_PEN, TOOL_ERASER):
                            color = BG_CANVAS if cur_tool == TOOL_ERASER else cur_color
                            pygame.draw.circle(canvas, color, start_pos, cur_size)

            # ── Mouse button up ───────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing and start_pos:
                    end_pos = to_canvas(*event.pos)
                    _finalize_shape(canvas, cur_tool, cur_color, cur_size, start_pos, end_pos)
                    drawing = False
                    preview = None
                    start_pos = None

            # ── Mouse motion ──────────────────────────────────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                cx, cy = to_canvas(*event.pos)
                if event.pos[1] >= TOOLBAR_H:
                    if cur_tool == TOOL_PEN:
                        rel = event.rel
                        pygame.draw.line(canvas, cur_color,
                                         (cx - rel[0], cy - rel[1]), (cx, cy),
                                         max(1, cur_size * 2))
                        pygame.draw.circle(canvas, cur_color, (cx, cy), cur_size)
                    elif cur_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, BG_CANVAS, (cx, cy), cur_size * 3)
                    else:
                        # Preview shapes
                        preview = canvas.copy()
                        _draw_preview(preview, cur_tool, cur_color, cur_size, start_pos, (cx, cy))

        # ── Drawing ───────────────────────────────────────────────────────
        screen.fill(BG_TOOLBAR)

        # Build display canvas (with live text preview on top)
        display = (preview if preview else canvas).copy()

        if cur_tool == TOOL_TEXT and text_active and text_pos:
            preview_txt = font.render(text_buffer + "|", True, cur_color)
            display.blit(preview_txt, text_pos)

        screen.blit(display, (0, TOOLBAR_H))
        draw_toolbar(screen, tool_buttons, cur_tool, cur_color, cur_size, palette_rects)

        # Cursor ring
        if mouse_pos[1] >= TOOLBAR_H:
            r = cur_size * 3 if cur_tool == TOOL_ERASER else max(cur_size, 2)
            pygame.draw.circle(screen, BORDER_CLR, mouse_pos, r, 1)

        pygame.display.flip()


def _finalize_shape(canvas, tool, color, size, sp, ep):
    """Commit a shape to canvas on mouse release."""
    if tool == TOOL_RECT:
        rx, ry = min(sp[0], ep[0]), min(sp[1], ep[1])
        rw, rh = abs(ep[0]-sp[0]), abs(ep[1]-sp[1])
        pygame.draw.rect(canvas, color, (rx, ry, rw, rh), size)

    elif tool == TOOL_CIRCLE:
        rad = int(math.hypot(ep[0]-sp[0], ep[1]-sp[1]))
        if rad > 0:
            pygame.draw.circle(canvas, color, sp, rad, size)

    elif tool == TOOL_LINE:
        pygame.draw.line(canvas, color, sp, ep, max(1, size))

    elif tool == TOOL_SQUARE:
        side = min(abs(ep[0]-sp[0]), abs(ep[1]-sp[1]))
        sx = sp[0] if ep[0] >= sp[0] else sp[0] - side
        sy = sp[1] if ep[1] >= sp[1] else sp[1] - side
        pygame.draw.rect(canvas, color, (sx, sy, side, side), size)

    elif tool == TOOL_RTRIANGLE:
        pts = [sp, (ep[0], sp[1]), (ep[0], ep[1])]
        pygame.draw.polygon(canvas, color, pts, size)

    elif tool == TOOL_ETRIANGLE:
        dx = ep[0] - sp[0]
        dy = ep[1] - sp[1]
        dist = math.hypot(dx, dy)
        mid_x = (sp[0] + ep[0]) / 2
        mid_y = (sp[1] + ep[1]) / 2
        apex_x = mid_x - dy * (math.sqrt(3)/2)
        apex_y = mid_y + dx * (math.sqrt(3)/2)
        pts = [sp, ep, (int(apex_x), int(apex_y))]
        pygame.draw.polygon(canvas, color, pts, size)

    elif tool == TOOL_RHOMBUS:
        cx = (sp[0] + ep[0]) // 2
        cy = (sp[1] + ep[1]) // 2
        pts = [(cx, sp[1]), (ep[0], cy), (cx, ep[1]), (sp[0], cy)]
        pygame.draw.polygon(canvas, color, pts, size)


def _draw_preview(surface, tool, color, size, sp, ep):
    """Draw shape preview on a surface copy."""
    if tool == TOOL_RECT:
        rx, ry = min(sp[0], ep[0]), min(sp[1], ep[1])
        rw, rh = abs(ep[0]-sp[0]), abs(ep[1]-sp[1])
        pygame.draw.rect(surface, color, (rx, ry, rw, rh), size)

    elif tool == TOOL_CIRCLE:
        rad = int(math.hypot(ep[0]-sp[0], ep[1]-sp[1]))
        if rad > 0:
            pygame.draw.circle(surface, color, sp, rad, size)

    elif tool == TOOL_LINE:
        pygame.draw.line(surface, color, sp, ep, max(1, size))

    elif tool == TOOL_SQUARE:
        side = min(abs(ep[0]-sp[0]), abs(ep[1]-sp[1]))
        sx = sp[0] if ep[0] >= sp[0] else sp[0] - side
        sy = sp[1] if ep[1] >= sp[1] else sp[1] - side
        pygame.draw.rect(surface, color, (sx, sy, side, side), size)

    elif tool == TOOL_RTRIANGLE:
        pts = [sp, (ep[0], sp[1]), (ep[0], ep[1])]
        pygame.draw.polygon(surface, color, pts, size)

    elif tool == TOOL_ETRIANGLE:
        dx = ep[0] - sp[0]
        dy = ep[1] - sp[1]
        mid_x = (sp[0] + ep[0]) / 2
        mid_y = (sp[1] + ep[1]) / 2
        apex_x = mid_x - dy * (math.sqrt(3)/2)
        apex_y = mid_y + dx * (math.sqrt(3)/2)
        pts = [sp, ep, (int(apex_x), int(apex_y))]
        pygame.draw.polygon(surface, color, pts, size)

    elif tool == TOOL_RHOMBUS:
        cx = (sp[0] + ep[0]) // 2
        cy = (sp[1] + ep[1]) // 2
        pts = [(cx, sp[1]), (ep[0], cy), (cx, ep[1]), (sp[0], cy)]
        pygame.draw.polygon(surface, color, pts, size)


if __name__ == "__main__":
    main()