import pygame
import math
import random
import os
import serial
import threading
import time

# Inisialisasi Pygame
pygame.init()

# --- Pengaturan Serial ---
try:
    COM_PORT = '/dev/ttyUSB0'
    ser = serial.Serial(COM_PORT, 9600, timeout=1)
    print(f"Berhasil terhubung ke port serial {COM_PORT}")
    serial_available = True
except serial.SerialException as e:
    print(f"Gagal terhubung ke port serial: {e}")
    print("Aplikasi akan berjalan tanpa input serial.")
    serial_available = False

# --- Variabel Komunikasi Antar Thread ---
serial_triggered_spin = False
running = True

# --- Fungsi Listener Serial ---
def listen_for_serial():
    global serial_triggered_spin, running
    while running:
        if serial_available and ser.in_waiting > 0:
            try:
                data = ser.read(1).decode('utf-8').strip()
                if data.lower() == 's':
                    print("Input 's' diterima dari serial, memutar roda...")
                    serial_triggered_spin = True
            except (UnicodeDecodeError, serial.SerialException):
                pass
        time.sleep(0.05)

# --- Pengaturan Awal (Mode Jendela) ---
INITIAL_WIDTH, INITIAL_HEIGHT = 540, 960
FPS = 60
is_fullscreen = False

screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("FTEK Jaya")

# --- Variabel Global untuk Tata Letak Dinamis ---
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
scaling_factor = 1.0; RADIUS, CENTER_X, CENTER_Y = 0, 0, 0
main_font, result_font, instruction_font, credit_font = None, None, None, None
POINTER_SIZE, POINTER_OFFSET, TEXT_OUTLINE_OFFSET = 0, 0, 0

# --- Warna & Hadiah ---
BLACK=(0,0,0); WHITE=(255,255,255); RED=(220,20,60); GRAY=(50,50,50); GOLD=(255,215,0)
WHEEL_COLORS=[(255,99,71), (255,165,0), (255,255,0), (50,205,50), (64,224,208), (0,191,255), (138,43,226), (128,128,128)]
visual_prizes=["Bolpen", "Keychain", "Tumbler", "Gelas", "Kipas", "Payung", "Motor", "Zonk"]
random.shuffle(visual_prizes)
winnable_prizes_pool = [
    "Bolpen", "Keychain", "Tumbler", "Gelas", "Kipas", "Payung", "Motor"] + ["Zonk"] * 63 # 7 Hadiah vs 63 Zonk -> Peluang menang 7/70 atau 10%

# --- Muat Aset Logo ---
try:
    logo_img = pygame.image.load('assets/logo_ftek.png').convert_alpha()
except pygame.error as e:
    print(f"Gagal memuat logo: {e}. Pastikan file 'assets/logo_ftek.png' ada.")
    logo_img = None

def recalculate_layout():
    global screen, scaling_factor, RADIUS, CENTER_X, CENTER_Y, SCREEN_WIDTH, SCREEN_HEIGHT
    global main_font, result_font, instruction_font, POINTER_SIZE, POINTER_OFFSET, TEXT_OUTLINE_OFFSET, credit_font
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size(); scaling_factor = SCREEN_HEIGHT / 960.0
    CENTER_X, CENTER_Y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    RADIUS = int(210 * scaling_factor); POINTER_SIZE = int(30 * scaling_factor)
    POINTER_OFFSET = int(18 * scaling_factor); TEXT_OUTLINE_OFFSET = max(1, int(2 * scaling_factor))
    main_font = pygame.font.SysFont('Arial', int(24 * scaling_factor), bold=True)
    result_font = pygame.font.SysFont('Arial', int(42 * scaling_factor), bold=True)
    instruction_font = pygame.font.SysFont('Arial', int(32 * scaling_factor), bold=True)
    credit_font = pygame.font.SysFont('Arial', int(22 * scaling_factor), bold=True)

# --- Variabel Animasi ---
angle, final_result = 0, ""; is_spinning = False
start_spin_time, start_angle, rotation_amount, idle_angle_offset = 0, 0, 0, 0
spin_duration = 5000

# --- Fungsi Drawing ---
def draw_wheel_and_text(surface, current_angle):
    num_segments = len(visual_prizes)
    angle_per_segment = 360 / num_segments
    for i, prize in enumerate(visual_prizes):
        points = [(CENTER_X, CENTER_Y)];
        for step in range(int(angle_per_segment) + 2):
            rad = math.radians(current_angle + i * angle_per_segment + step)
            x = CENTER_X + RADIUS * math.cos(rad); y = CENTER_Y + RADIUS * math.sin(rad)
            points.append((x, y))
        pygame.draw.polygon(surface, WHEEL_COLORS[i], points)
        pygame.draw.polygon(surface, BLACK, points, max(1, int(2 * scaling_factor)))
        text_angle_rad = math.radians(current_angle + i * angle_per_segment + angle_per_segment / 2)
        text_x = CENTER_X + (RADIUS * 0.65) * math.cos(text_angle_rad); text_y = CENTER_Y + (RADIUS * 0.65) * math.sin(text_angle_rad)
        text_surface = main_font.render(prize, True, BLACK); outline_surface = main_font.render(prize, True, WHITE)
        angle_deg = -math.degrees(text_angle_rad)
        rotated_text = pygame.transform.rotate(text_surface, angle_deg); rotated_outline = pygame.transform.rotate(outline_surface, angle_deg)
        outline_pos = rotated_outline.get_rect(center=(text_x, text_y))
        surface.blit(rotated_outline, (outline_pos.x, outline_pos.y - TEXT_OUTLINE_OFFSET)); surface.blit(rotated_outline, (outline_pos.x, outline_pos.y + TEXT_OUTLINE_OFFSET)); surface.blit(rotated_outline, (outline_pos.x - TEXT_OUTLINE_OFFSET, outline_pos.y)); surface.blit(rotated_outline, (outline_pos.x + TEXT_OUTLINE_OFFSET, outline_pos.y))
        text_pos = rotated_text.get_rect(center=(text_x, text_y)); surface.blit(rotated_text, text_pos)

def draw_ui(surface):
    pointer_points = [(CENTER_X + RADIUS - TEXT_OUTLINE_OFFSET, CENTER_Y), (CENTER_X + RADIUS + POINTER_SIZE, CENTER_Y - POINTER_OFFSET), (CENTER_X + RADIUS + POINTER_SIZE, CENTER_Y + POINTER_OFFSET)]
    pygame.draw.polygon(surface, RED, pointer_points); pygame.draw.circle(surface, BLACK, (CENTER_X, CENTER_Y), int(25 * scaling_factor))
    if not is_spinning and final_result:
        if final_result == "Zonk":
            header_text_surf = result_font.render("Anda Kurang Beruntung", True, WHITE)
            prize_text_surf = main_font.render("Silakan coba lagi!", True, WHITE)
        else:
            header_text_surf = result_font.render("Selamat!", True, GOLD)
            prize_text_surf = main_font.render(f"Anda mendapatkan: {final_result}", True, WHITE)
        surface.blit(header_text_surf, header_text_surf.get_rect(center=(CENTER_X, int(120 * scaling_factor)))); surface.blit(prize_text_surf, prize_text_surf.get_rect(center=(CENTER_X, int(180 * scaling_factor))))
    elif not is_spinning:
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        alpha = 155 + (pulse * 100)
        instruction_text = instruction_font.render("Tekan Spasi!", True, (255, 255, 255, alpha))
        surface.blit(instruction_text, instruction_text.get_rect(center=(CENTER_X, int(120 * scaling_factor))))

def draw_credits(surface):
    margin = int(20 * scaling_factor)
    if logo_img:
        logo_base_height = 150 
        scaled_logo_height = int(logo_base_height * scaling_factor)
        scaled_logo_width = int(logo_img.get_width() * (scaled_logo_height / logo_img.get_height()))
        scaled_logo = pygame.transform.smoothscale(logo_img, (scaled_logo_width, scaled_logo_height))
        logo_rect = scaled_logo.get_rect(bottomleft=(margin, SCREEN_HEIGHT - margin))
        surface.blit(scaled_logo, logo_rect)
        credit_text = credit_font.render("Made with love by", True, (200, 200, 200))
        credit_rect = credit_text.get_rect(bottomleft=(margin, logo_rect.top - int(5 * scaling_factor)))
        surface.blit(credit_text, credit_rect)
    else:
        credit_text = credit_font.render("Made with love by FTEK", True, (200, 200, 200))
        credit_rect = credit_text.get_rect(bottomleft=(margin, SCREEN_HEIGHT - margin))
        surface.blit(credit_text, credit_rect)

# --- Panggil kalkulasi tata letak untuk pertama kali ---
recalculate_layout()
clock = pygame.time.Clock()

# --- Mulai Thread Serial Listener ---
if serial_available:
    serial_thread = threading.Thread(target=listen_for_serial, daemon=True)
    serial_thread.start()

# --- Game Loop Utama ---
while running:
    spin_now = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                if is_fullscreen: screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else: screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
                recalculate_layout()
            if event.key == pygame.K_SPACE:
                spin_now = True

    if serial_triggered_spin:
        spin_now = True
        serial_triggered_spin = False

    if spin_now and not is_spinning:
        if winnable_prizes_pool:
            winner = random.choice(winnable_prizes_pool); final_result = winner
            if winner != "Zonk":
                winnable_prizes_pool.remove(winner)
        else:
            final_result = "Zonk"
        
        if final_result in visual_prizes:
            target_index = visual_prizes.index(final_result)
        else:
            target_index = visual_prizes.index("Zonk")

        angle_per_segment = 360 / len(visual_prizes)
        destination_pointer_angle = (target_index * angle_per_segment) + (angle_per_segment / 2) + random.uniform(-15, 15)
        final_wheel_angle = (360 - destination_pointer_angle) % 360
        is_spinning = True; start_spin_time = pygame.time.get_ticks(); start_angle = angle
        full_rotations = random.randint(4, 6) * 360
        rotation_amount = full_rotations - (start_angle % 360) + final_wheel_angle
    
    if is_spinning:
        elapsed_time = pygame.time.get_ticks() - start_spin_time
        if elapsed_time < spin_duration:
            progress = elapsed_time / spin_duration
            eased_progress = 1 - pow(1 - progress, 4)
            angle = start_angle + rotation_amount * eased_progress
        else:
            angle = start_angle + rotation_amount
            is_spinning = False
            # --- BARIS TAMBAHAN ---
            # Cek jika serial tersedia dan hasilnya bukan Zonk
            if serial_available and final_result != "Zonk":
                try:
                    # Kirim karakter 'b' sebagai bytes
                    ser.write(b'b')
                    print(f"Hadiah: {final_result}. Mengirim 'b' via serial.")
                except serial.SerialException as e:
                    print(f"Gagal mengirim data serial: {e}")
            # --- AKHIR DARI BARIS TAMBAHAN ---

    else:
        idle_angle_offset = math.sin(pygame.time.get_ticks() * 0.002) * 2.5

    # Drawing
    screen.fill(GRAY)
    draw_angle = angle + (idle_angle_offset if not is_spinning else 0)
    draw_wheel_and_text(screen, draw_angle)
    draw_ui(screen)
    draw_credits(screen)
    pygame.display.flip()
    clock.tick(FPS)

# --- Tutup Aplikasi ---
if serial_available:
    ser.close()
pygame.quit()