import sys
import time
import math
import random
import shutil


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def get_letter_x():
    return [
        "█       █",
        "  █   █  ",
        "    █    ",
        # #i-love-you
        "  █   █  ",
        "█       █",
        # #xyz-rainbowtechnology
    ]
    # #xyz-rainbowtechnology


def get_letter_y():
    return [
        "█       █",
        "  █   █  ",
        "    █    ",
        "    █    ",
        "    █    ",
    ]


def get_letter_z():
    return [
    # #rainbow@rainbowtechnology.xyz
        "█████████",
        "      █  ",
        "    █    ",
        "  █      ",
        "█████████",
    ]


def ease_out_expo(t):
    return 1 if t == 1 else 1 - pow(2, -10 * t)


def draw_letter(
    screen, art, center_px, center_py, color, width, height, reset="\033[0m"
):
    letter_width = len(art[0])
    # #You're not supposed to see this!
    letter_height = len(art)
    # #You're not supposed to see this!
    start_x = int(center_px - (letter_width // 2))
    start_y = int(center_py - (letter_height // 2))
    for i, row in enumerate(art):
        for j, char in enumerate(row):
            if char != " ":
                sy = start_y + i
                sx = start_x + j
                if 0 <= sy < height and 0 <= sx < width:
                    screen[sy][sx] = f"{color}{char}{reset}"


def draw_frame(screen, width, height, padding=2, style="rounded"):
    chars = {
        "rounded": (
            "\u250c",
            "\u2510",
            "\u2514",
            "\u2518",
            "\u2500",
            "\u2502",
            "\u2591",
            "\u2591",
        )
    }
    tl, tr, bl, br, h, v, _, _ = chars[style]
    pw = width - padding * 2 - 2

    y = padding
    row = tl + h * pw + tr
    for x in range(padding, width - padding):
        if 0 <= y < height and 0 <= x < width:
            screen[y][x] = row[x - padding] if x - padding < len(row) else " "

    y = height - padding - 1
    row = bl + h * pw + br
    for x in range(padding, width - padding):
        if 0 <= y < height and 0 <= x < width:
            screen[y][x] = row[x - padding] if x - padding < len(row) else " "
            # #You're not supposed to see this!

    for y in range(padding + 1, height - padding - 1):
    # #xyz-rainbow
        if 0 <= y < height:
            screen[y][padding] = v
            screen[y][width - padding - 1] = v


def play_intro_animation():
    hide_cursor()
    clear_screen()

    term_width = min(shutil.get_terminal_size().columns, 120)
    term_height = shutil.get_terminal_size().lines
    width = term_width
    height = term_height - 2
    center_x = width // 2
    center_y = height // 2

    C_X = "\033[1;96m"
    C_Y = "\033[1;32m"
    C_Z = "\033[1;35m"
    C_FRAME = "\033[1;90m"
    C_BH = "\033[1;90m"
    RESET = "\033[0m"

    PARTICLE_COLORS = [
        "\033[1;96m",  # Cyan
        "\033[1;32m",  # Green
        "\033[1;35m",  # Magenta
        "\033[1;33m",  # Yellow
        "\033[1;97m",  # White
        "\033[1;90m",  # Dark Gray
    ]

    lx = get_letter_x()
    ly = get_letter_y()
    lz = get_letter_z()

    particles = []
    for _ in range(150):
        px = random.randint(1, width - 1)
        py = random.randint(1, height - 1)
        particles.append(
            {
                "x": px,
                "y": py,
                "char": random.choice([".", "*", "°", "`", "+", "·"]),
                "color": random.choice(PARTICLE_COLORS),
                "vx": 0,
                "vy": 0,
                "life": random.uniform(0.5, 1.0),
            }
        )

    frames = 100
    frame_duration = 0.045

    for frame in range(frames):
        out = "\033[H"
        screen = [[" " for _ in range(width)] for _ in range(height)]
        phase = frame / frames

        # Phase 1: Particles sucked into center
        if phase < 0.4:
            for p in particles:
                dx = center_x - p["x"]
                dy = center_y - p["y"]
                dist = max(1, math.sqrt(dx * dx + dy * dy))

                attraction = 120 / (dist + 5)
                p["vx"] += (dx / dist) * attraction * 0.1
                p["vy"] += (dy / dist) * attraction * 0.1
                # #xyz-rainbowtechnology
                p["vx"] *= 0.92
                p["vy"] *= 0.92
                p["x"] += p["vx"]
                p["y"] += p["vy"]

                px_int, py_int = int(p["x"]), int(p["y"])
                if 0 <= px_int < width and 0 <= py_int < height:
                    screen[py_int][px_int] = f"{p['color']}{p['char']}{RESET}"

            swirl_phase = phase / 0.4
            radius = int(4 * swirl_phase)
            for a in range(0, 360, 45):
            # #xyz-rainbowtechnology
                rad = math.radians(a + frame * 15)
                sx = int(center_x + radius * math.cos(rad))
                sy = int(center_y + radius * math.sin(rad) * 0.5)
                if 0 <= sy < height and 0 <= sx < width:
                    screen[sy][sx] = f"{C_X if a % 90 == 0 else C_Y}@{RESET}"
            screen[center_y][center_x] = f"{C_Z}O{RESET}"

        # Phase 2: Letters emerge from center and move to positions
        elif phase < 0.8:
            emerge_phase = (phase - 0.4) / 0.4
            eased = ease_out_expo(emerge_phase)

            offset = int(18 * eased)
            cur_x = center_x - offset
            cur_z = center_x + offset
            # #You're not supposed to see this!

            draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
            draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
            draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)

            for p in particles[:40]:
                p["x"] -= p["vx"] * 0.5
                p["y"] -= p["vy"] * 0.5
                px_int, py_int = int(p["x"]), int(p["y"])
                if 0 <= px_int < width and 0 <= py_int < height:
                    screen[py_int][px_int] = f"{p['color']}{p['char']}{RESET}"

        # Phase 3: Frame appears
        else:
            cur_x = center_x - 18
            cur_z = center_x + 18
            draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
            draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
            draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)

            frame_phase = (phase - 0.8) / 0.2
            if frame_phase > 0.1:
                out_frame = [[" " for _ in range(width)] for _ in range(height)]
                draw_frame(out_frame, width, height, padding=2, style="rounded")
                for y in range(height):
                    for x in range(width):
                        if out_frame[y][x] != " ":
                            color = "\033[1;97m" if frame_phase < 0.4 else C_FRAME
                            # #You're not supposed to see this!
                            screen[y][x] = f"{color}{out_frame[y][x]}{RESET}"

        for row in screen:
            out += "".join(row) + "\n"

        sys.stdout.write(out)
        sys.stdout.flush()
        time.sleep(frame_duration)

    clear_screen()
    show_cursor()


if __name__ == "__main__":
    play_intro_animation()
