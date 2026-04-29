import pygame
import sys
import math

from paint import (
    ToolButton, draw_toolbar, to_canvas,
    draw_square, draw_right_triangle,
    draw_equilateral_triangle, draw_rhombus,
    screen, clock, canvas, font,
    SCREEN_W, SCREEN_H, TOOLBAR_H,
    BG_CANVAS, BG_TOOLBAR, BORDER_CLR,
    PALETTE,
    TOOL_PEN, TOOL_RECT, TOOL_CIRCLE, TOOL_ERASER,
    TOOL_SQUARE, TOOL_RTRI, TOOL_ETRI, TOOL_RHOMBUS,
    plus_rect, minus_rect, clear_rect,
)


def main():
    # ─── Кнопки инструментов ──────────────────────────────────────────────
    # Первый ряд: базовые инструменты
    # Второй ряд: новые фигуры
    tool_buttons = [
        ToolButton( 10, 5,  68, 26, "✏ Pen",     TOOL_PEN),
        ToolButton( 84, 5,  72, 26, "▭ Rect",     TOOL_RECT),
        ToolButton(162, 5,  76, 26, "○ Circle",   TOOL_CIRCLE),
        ToolButton(244, 5,  72, 26, "⌫ Erase",    TOOL_ERASER),
        # Новые фигуры — второй ряд
        ToolButton( 10, 35, 68, 26, "■ Square",   TOOL_SQUARE),
        ToolButton( 84, 35, 72, 26, "◺ R.Tri",    TOOL_RTRI),
        ToolButton(162, 35, 76, 26, "△ E.Tri",    TOOL_ETRI),
        ToolButton(244, 35, 72, 26, "◇ Rhombus",  TOOL_RHOMBUS),
    ]

    # Вычисляем прямоугольники для ячеек палитры
    palette_rects = []
    for i in range(len(PALETTE)):
        rx = 545 + (i % 9) * 22   # x позиция ячейки (9 в ряд)
        ry = 5  + (i // 9) * 22   # y позиция (новый ряд каждые 9 цветов)
        palette_rects.append(pygame.Rect(rx, ry, 20, 20))

    cur_tool  = TOOL_PEN
    cur_color = (0, 0, 0)
    cur_size  = 4
    drawing   = False
    start_pos = None
    preview   = None   # временная копия холста для предпросмотра фигур

    # Инструменты, использующие предпросмотр при перетаскивании
    SHAPE_TOOLS = (TOOL_RECT, TOOL_CIRCLE, TOOL_SQUARE,
                   TOOL_RTRI, TOOL_ETRI, TOOL_RHOMBUS)

    while True:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ─── Нажатие кнопки мыши ──────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos

                if y < TOOLBAR_H:
                    # Клик по панели инструментов

                    # Проверяем кнопки инструментов
                    for btn in tool_buttons:
                        if btn.is_clicked((x, y)):
                            cur_tool = btn.tool_id

                    # Проверяем ячейки палитры
                    for idx, rect in enumerate(palette_rects):
                        if rect.collidepoint(x, y):
                            cur_color = PALETTE[idx]

                    # Кнопки размера
                    if plus_rect.collidepoint(x, y):
                        cur_size = min(50, cur_size + 1)
                    elif minus_rect.collidepoint(x, y):
                        cur_size = max(1, cur_size - 1)
                    elif clear_rect.collidepoint(x, y):
                        canvas.fill(BG_CANVAS)   # очистить холст

                else:
                    # Клик по холсту — начинаем рисование
                    drawing   = True
                    start_pos = to_canvas(x, y)
                    if cur_tool in (TOOL_PEN, TOOL_ERASER):
                        # Для карандаша и ластика сразу ставим точку
                        color = BG_CANVAS if cur_tool == TOOL_ERASER else cur_color
                        pygame.draw.circle(canvas, color, start_pos, cur_size)

            # ─── Отпускание кнопки мыши — фиксируем фигуру ───────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing and start_pos:
                    end_pos = to_canvas(*event.pos)

                    if cur_tool == TOOL_RECT:
                        rx = min(start_pos[0], end_pos[0])
                        ry = min(start_pos[1], end_pos[1])
                        rw = abs(end_pos[0] - start_pos[0])
                        rh = abs(end_pos[1] - start_pos[1])
                        pygame.draw.rect(canvas, cur_color, (rx, ry, rw, rh), cur_size)

                    elif cur_tool == TOOL_CIRCLE:
                        rad = int(math.hypot(end_pos[0] - start_pos[0],
                                             end_pos[1] - start_pos[1]))
                        if rad > 0:
                            pygame.draw.circle(canvas, cur_color, start_pos, rad, cur_size)

                    elif cur_tool == TOOL_SQUARE:
                        draw_square(canvas, cur_color, start_pos, end_pos, cur_size)

                    elif cur_tool == TOOL_RTRI:
                        draw_right_triangle(canvas, cur_color, start_pos, end_pos, cur_size)

                    elif cur_tool == TOOL_ETRI:
                        draw_equilateral_triangle(canvas, cur_color, start_pos, end_pos, cur_size)

                    elif cur_tool == TOOL_RHOMBUS:
                        draw_rhombus(canvas, cur_color, start_pos, end_pos, cur_size)

                    drawing = False
                    preview = None   # сбрасываем предпросмотр

            # ─── Движение мыши — рисование и предпросмотр ─────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                cx, cy = to_canvas(*event.pos)
                if event.pos[1] >= TOOLBAR_H:

                    if cur_tool == TOOL_PEN:
                        # Рисуем линию между предыдущей и текущей позицией
                        rel = event.rel
                        pygame.draw.line(canvas, cur_color,
                                         (cx - rel[0], cy - rel[1]),
                                         (cx, cy), cur_size * 2)
                        pygame.draw.circle(canvas, cur_color, (cx, cy), cur_size)

                    elif cur_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, BG_CANVAS, (cx, cy), cur_size * 3)

                    elif cur_tool in SHAPE_TOOLS:
                        # Предпросмотр: рисуем на копии холста, не трогая оригинал
                        preview = canvas.copy()
                        if cur_tool == TOOL_RECT:
                            rx = min(start_pos[0], cx)
                            ry = min(start_pos[1], cy)
                            rw = abs(cx - start_pos[0])
                            rh = abs(cy - start_pos[1])
                            pygame.draw.rect(preview, cur_color, (rx, ry, rw, rh), cur_size)
                        elif cur_tool == TOOL_CIRCLE:
                            rad = int(math.hypot(cx - start_pos[0], cy - start_pos[1]))
                            pygame.draw.circle(preview, cur_color, start_pos, rad, cur_size)
                        elif cur_tool == TOOL_SQUARE:
                            draw_square(preview, cur_color, start_pos, (cx, cy), cur_size)
                        elif cur_tool == TOOL_RTRI:
                            draw_right_triangle(preview, cur_color, start_pos, (cx, cy), cur_size)
                        elif cur_tool == TOOL_ETRI:
                            draw_equilateral_triangle(preview, cur_color, start_pos, (cx, cy), cur_size)
                        elif cur_tool == TOOL_RHOMBUS:
                            draw_rhombus(preview, cur_color, start_pos, (cx, cy), cur_size)

            # ─── Колесо мыши: изменение размера кисти ─────────────────────
            if event.type == pygame.MOUSEWHEEL:
                cur_size = max(1, min(50, cur_size + event.y))

        # ─── Отрисовка кадра ──────────────────────────────────────────────
        screen.fill(BG_TOOLBAR)
        # Показываем предпросмотр (если есть) или обычный холст
        screen.blit(preview if preview else canvas, (0, TOOLBAR_H))
        draw_toolbar(screen, tool_buttons, cur_tool, cur_color, cur_size, palette_rects)

        # Курсор: кружок размером кисти/ластика
        if mouse_pos[1] >= TOOLBAR_H:
            r = cur_size * 3 if cur_tool == TOOL_ERASER else cur_size
            pygame.draw.circle(screen, BORDER_CLR, mouse_pos, max(r, 2), 1)

        pygame.display.flip()


if __name__ == "__main__":
    main()