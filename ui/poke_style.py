# =============================================================================
# UI/POKE_STYLE.PY  –  Shared Pokemon DA palette + helpers
# =============================================================================
import pygame
from config.settings import PROJECT_ROOT

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
C_BG_TOP   = ( 10,  14,  38)
C_BG_BTM   = ( 22,  32,  70)
C_STRIPE   = ( 28,  38,  80)
C_PANEL    = ( 16,  22,  52)
C_GOLD     = (255, 203,   5)
C_GOLD_DIM = (155, 124,   4)
C_WHITE    = (235, 235, 235)
C_GRAY     = (115, 115, 135)
C_BLACK    = (  0,   0,   0)
C_GREEN    = ( 80, 210, 100)
C_BLUE     = ( 90, 160, 255)

# ---------------------------------------------------------------------------
# Font loader
# ---------------------------------------------------------------------------
def font(size, hollow=False):
    name = "Pokemon_Hollow.ttf" if hollow else "Pokemon_Solid.ttf"
    path = PROJECT_ROOT / "assets" / "font" / name
    try:
        return pygame.font.Font(str(path), size)
    except Exception:
        return pygame.font.Font(None, size + 10)

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def make_gradient_bg(w, h):
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        r = int(C_BG_TOP[0] + (C_BG_BTM[0] - C_BG_TOP[0]) * t)
        g = int(C_BG_TOP[1] + (C_BG_BTM[1] - C_BG_TOP[1]) * t)
        b = int(C_BG_TOP[2] + (C_BG_BTM[2] - C_BG_TOP[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
    for i in range(-h, w + h, 120):
        pts = [(i, 0), (i+70, 0), (i+70+h, h), (i+h, h)]
        pygame.draw.polygon(surf, C_STRIPE, pts)
    return surf


def panel(screen, x, y, w, h, border=None, alpha=215):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((*C_PANEL, alpha))
    screen.blit(surf, (x, y))
    pygame.draw.rect(screen, border or C_GOLD_DIM, (x, y, w, h), 2)


def corner_accents(screen, x, y, w, h, color=None, size=14):
    c = color or C_GOLD
    for ax, dx in ((x, 1), (x + w, -1)):
        for ay, dy in ((y, 1), (y + h, -1)):
            pygame.draw.line(screen, c, (ax, ay), (ax + dx * size, ay), 2)
            pygame.draw.line(screen, c, (ax, ay), (ax, ay + dy * size), 2)


def text_c(screen, fnt, text, color, cx, y, shadow=False):
    """Blit text centered on cx."""
    surf = fnt.render(text, True, color)
    x = cx - surf.get_width() // 2
    if shadow:
        sh = fnt.render(text, True, C_BLACK)
        screen.blit(sh, (x + 2, y + 2))
    screen.blit(surf, (x, y))


def blit_clipped(screen, surf, x, y, max_w):
    if surf.get_width() > max_w:
        surf = surf.subsurface((0, 0, max_w, surf.get_height()))
    screen.blit(surf, (x, y))


def wrap(fnt, text, max_w):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        cand = (cur + " " + word).strip()
        if fnt.size(cand)[0] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def fit_and_crop(sprite, target_w, target_h):
    """Scale sprite to fill target_h, then center-crop to target_w."""
    if sprite is None:
        return None
    sw, sh = sprite.get_size()
    scale = target_h / sh
    nw = int(sw * scale)
    nh = target_h
    scaled = pygame.transform.scale(sprite, (nw, nh))
    if nw > target_w:
        ox = (nw - target_w) // 2
        return scaled.subsurface((ox, 0, target_w, nh))
    return scaled
