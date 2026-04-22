import pygame
import sys
import math

from paint import (
    ToolButton, draw_toolbar, to_canvas,
    screen, clock, canvas, font,
    SCREEN_W, SCREEN_H, TOOLBAR_H,
    BG_CANVAS, BG_TOOLBAR, BORDER_CLR,
    PALETTE, TOOL_PEN, TOOL_RECT, TOOL_CIRCLE, TOOL_ERASER,
    plus_rect, minus_rect, clear_rect,
)


# Main loop
def main():
    tool_buttons = [
        ToolButton( 10, 15, 70, 34, " Pen",    TOOL_PEN),
        ToolButton( 88, 15, 80, 34, "▭ Rect",   TOOL_RECT),
        ToolButton(176, 15, 80, 34, "○ Circle", TOOL_CIRCLE),
        ToolButton(264, 15, 58, 34, "⌫ Erase",  TOOL_ERASER),
    ]

    palette_rects = []
    for i in range(len(PALETTE)): #
        rx = 455 + (i % 9) * 22 #calculate the x position for each color square in the palette, arranging them in rows of 9
        ry = 5 + (i // 9) * 22 #calculate the y position for each color square, moving to the next row after every 9 colors
        palette_rects.append(pygame.Rect(rx, ry, 20, 20)) 

    cur_tool  = TOOL_PEN
    cur_color = (0, 0, 0)
    cur_size  = 4
    drawing   = False
    start_pos = None
    preview   = None

    while True:
        clock.tick(60) 
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos

                if y < TOOLBAR_H: 
                    # Check tool buttons
                    for btn in tool_buttons: 
                        if btn.is_clicked((x, y)):
                            cur_tool = btn.tool_id #update the current tool to the one represented by the clicked button

                    # Palette
                    for idx, rect in enumerate(palette_rects): #check if the click was on any of the color palette squares, and if so, update the current color to the corresponding color from the PALETTE list
                        if rect.collidepoint(x, y):
                            cur_color = PALETTE[idx]

                    # Size and clear buttons
                    if plus_rect.collidepoint(x, y): 
                        cur_size = min(50, cur_size + 1)
                    elif minus_rect.collidepoint(x, y):
                        cur_size = max(1, cur_size - 1)
                    elif clear_rect.collidepoint(x, y):
                        canvas.fill(BG_CANVAS)

                else: # Click on canvas 
                    drawing = True
                    start_pos = to_canvas(x, y)
                    if cur_tool in (TOOL_PEN, TOOL_ERASER):
                        color = BG_CANVAS if cur_tool == TOOL_ERASER else cur_color
                        pygame.draw.circle(canvas, color, start_pos, cur_size) #for pen and eraser, draw a circle at the starting position to create an initial mark on the canvas when the user starts drawing

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1: 
                if drawing:
                    end_pos = to_canvas(*event.pos) 
                    if cur_tool == TOOL_RECT and start_pos:
                        rx, ry = min(start_pos[0], end_pos[0]), min(start_pos[1], end_pos[1])#
                        rw, rh = abs(end_pos[0] - start_pos[0]), abs(end_pos[1] - start_pos[1])
                        pygame.draw.rect(canvas, cur_color, (rx, ry, rw, rh), cur_size) # calculate the final shape based on the starting and ending positions and draw it onto the canvas
                    elif cur_tool == TOOL_CIRCLE and start_pos:
                        rad = int(math.hypot(end_pos[0]-start_pos[0], end_pos[1]-start_pos[1])) #calculate the radius of the circle based on the distance between the starting and ending positions, and draw the circle onto the canvas
                        if rad > 0:
                            pygame.draw.circle(canvas, cur_color, start_pos, rad, cur_size)

                    drawing = False
                    preview = None

            if event.type == pygame.MOUSEMOTION and drawing: #when mouse is moving and clicked
                cx, cy = to_canvas(*event.pos) #convert the current mouse position to canvas coordinates
                if event.pos[1] >= TOOLBAR_H: #only draw on the canvas area, not the toolbar
                    if cur_tool == TOOL_PEN: 
                        rel = event.rel #movement changing
                        pygame.draw.line(canvas, cur_color, (cx - rel[0], cy - rel[1]), (cx, cy), cur_size * 2) #connect points
                        pygame.draw.circle(canvas, cur_color, (cx, cy), cur_size) # smooth line
                    elif cur_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, BG_CANVAS, (cx, cy), cur_size * 3)
                    elif cur_tool in (TOOL_RECT, TOOL_CIRCLE): #preview of figure
                        preview = canvas.copy() #create a copy of the current canvas to draw the preview on
                        if cur_tool == TOOL_RECT:
                            rx, ry = min(start_pos[0], cx), min(start_pos[1], cy)
                            rw, rh = abs(cx - start_pos[0]), abs(cy - start_pos[1])
                            pygame.draw.rect(preview, cur_color, (rx, ry, rw, rh), cur_size)
                        else:
                            rad = int(math.hypot(cx - start_pos[0], cy - start_pos[1])) #calculate the radius for the circle 
                            pygame.draw.circle(preview, cur_color, start_pos, rad, cur_size)

            if event.type == pygame.MOUSEWHEEL:
                cur_size = max(1, min(50, cur_size + event.y))

        # Drawing
        screen.fill(BG_TOOLBAR)
        screen.blit(preview if preview else canvas, (0, TOOLBAR_H))  # выводим холст ниже тулбара
        draw_toolbar(screen, tool_buttons, cur_tool, cur_color, cur_size, palette_rects)

        # Cursor preview
        if mouse_pos[1] >= TOOLBAR_H:
            c = BORDER_CLR
            r = cur_size * 3 if cur_tool == TOOL_ERASER else cur_size
            pygame.draw.circle(screen, c, mouse_pos, max(r, 2), 1)

        pygame.display.flip()

if __name__ == "__main__":
    main()