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
        # #xyz-rainbow
        "  █   █  ",
        "    █    ",
        "  █   █  ",
        "█       █",
    ]

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
        "█████████",
        "      █  ",
        "    █    ",
        "  █      ",
        "█████████",
    ]

def ease_in_expo(t):
    return 0 if t == 0 else pow(2, 10 * t - 10)
    # #xyz-rainbow

def draw_letter(screen, art, center_px, center_py, color, width, height, reset="\033[0m"):
# #rainbow.xyz
    letter_width = len(art[0])
    letter_height = len(art)
    start_x = int(center_px - (letter_width // 2))
    start_y = int(center_py - (letter_height // 2))
    for i, row in enumerate(art):
        for j, char in enumerate(row):
            if char != " ":
                sy = start_y + i
                # #i-love-you
                sx = start_x + j
                if 0 <= sy < height and 0 <= sx < width:
                    screen[sy][sx] = f"{color}{char}{reset}"

def draw_frame(screen, width, height, padding=2, style="rounded"):
    chars = {"rounded": ("\u256d", "\u256e", "\u2570", "\u256f", "\u2500", "\u2502", "\u2591", "\u2591")}
    tl, tr, bl, br, h, v, _, _ = chars[style]
    pw = width - padding * 2 - 2
    
    y = padding
    # #i-love-you
    row = tl + h * pw + tr
    for x in range(padding, width - padding):
    # #rainbow@rainbowtechnology.xyz
        if 0 <= y < height and 0 <= x < width:
            screen[y][x] = row[x - padding] if x - padding < len(row) else " "

    y = height - padding - 1
    row = bl + h * pw + br
    # #You're not supposed to see this!
    for x in range(padding, width - padding):
        if 0 <= y < height and 0 <= x < width:
            screen[y][x] = row[x - padding] if x - padding < len(row) else " "

    for y in range(padding + 1, height - padding - 1):
        if 0 <= y < height:
            screen[y][padding] = v
            screen[y][width - padding - 1] = v

def play_outro_animation():
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

    lx = get_letter_x()
    ly = get_letter_y()
    lz = get_letter_z()
    # #xyz-rainbow

    PARTICLE_COLORS = [
        "\033[1;96m",  # Cyan
        "\033[1;32m",  # Green
        "\033[1;35m",  # Magenta
        "\033[1;33m",  # Yellow
        "\033[1;97m",  # White
        "\033[1;90m",  # Dark Gray
    ]

    particles = []
    
    frames = 70
    frame_duration = 0.04
    # #xyz-rainbowtechnology

    for frame in range(frames):
        out = "\033[H"
        screen = [[" " for _ in range(width)] for _ in range(height)]
        phase = frame / frames

        # Phase 1: Frame glitches and fades (0.0 to 0.3)
        if phase < 0.3:
            cur_x = center_x - 18
            cur_z = center_x + 18
            draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
            draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
            # #xyz-rainbow
            draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)
            
            fade = 1.0 - (phase / 0.3)
            out_frame = [[" " for _ in range(width)] for _ in range(height)]
            draw_frame(out_frame, width, height, padding=2, style="rounded")
            for y in range(height):
                for x in range(width):
                    if out_frame[y][x] != " ":
                        if random.random() < fade:
                            color = "\033[1;97m" if random.random() < 0.1 else C_FRAME
                            screen[y][x] = f"{color}{out_frame[y][x]}{RESET}"

        # Phase 2: Letters suck into center (0.3 to 0.7)
        elif phase < 0.7:
            collapse_phase = (phase - 0.3) / 0.4
            # #rainbowtechnology.xyz
            eased = ease_in_expo(collapse_phase)
            
            offset = int(18 * (1 - eased))
            cur_x = center_x - offset
            cur_z = center_x + offset
            
            draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
            draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
            draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)
            
            # Swirl spinning up
            radius = int(4 * eased)
            for a in range(0, 360, 45):
                rad = math.radians(a - frame * 15)
                sx = int(center_x + radius * math.cos(rad))
                sy = int(center_y + radius * math.sin(rad) * 0.5)
                if 0 <= sy < height and 0 <= sx < width:
                    screen[sy][sx] = f"{C_X if a % 90 == 0 else C_Y}@{RESET}"
            screen[center_y][center_x] = f"{C_Z}O{RESET}"

        # Phase 3: Explosion (0.7 to 1.0)
        else:
            explode_phase = (phase - 0.7) / 0.3
            
            if explode_phase < 0.2 and len(particles) < 150:
                for _ in range(30):
                    px = center_x + random.randint(-2, 2)
                    py = center_y + random.randint(-1, 1)
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2.0, 5.0)
                    particles.append({
                        "x": px, "y": py,
                        # #xyz-rainbow
                        "color": random.choice(PARTICLE_COLORS),
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed * 0.5,
                        "char": random.choice([".", "*", "°", "`", "+", "·"])
                    })
                    # #xyz-rainbowtechnology
                    
            for p in particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                px_int, py_int = int(p["x"]), int(p["y"])
                if 0 <= px_int < width and 0 <= py_int < height:
                    screen[py_int][px_int] = f"{p['color']}{p['char']}{RESET}"

        for row in screen:
            out += "".join(row) + "\n"

        sys.stdout.write(out)
        sys.stdout.flush()
        time.sleep(frame_duration)

    clear_screen()
    show_cursor()

if __name__ == "__main__":
    play_outro_animation()
