import os
import math
import zipfile
import shutil
from PIL import Image, ImageChops, ImageDraw, ImageFilter

def draw_circles_frame(width, height, frame_idx, total_frames):
    """Часть 0: 6 кружков кружатся по орбите и сближаются к центру"""
    frame = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(frame)
    
    center_x, center_y = width // 2, height // 2
    progress = frame_idx / total_frames
    
    angle_offset = progress * (2 * math.pi) * 2
    base_radius = int((height * 0.25) * (1.0 - progress ** 2))
    
    num_circles = 6
    for i in range(num_circles):
        angle = (i * (2 * math.pi) / num_circles) + angle_offset
        cx = center_x + int(base_radius * math.cos(angle))
        cy = center_y + int(base_radius * math.sin(angle))
        
        r = int(20 - progress * 4 + (progress ** 3) * 15)
        
        alpha = 255
        if progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))
            
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, alpha))
        
    return frame

def create_slanted_soft_shine(width, height, offset, shine_width=500):
    """Генерация ультра-мягкой световой волны под аккуратным наклоном"""
    gradient = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(gradient)
    
    for x in range(shine_width):
        factor = (1.0 + math.cos(math.pi * abs(x - shine_width // 2) / (shine_width // 2))) / 2.0
        alpha = int(255 * factor)
        
        current_x = offset + x - (shine_width // 2)
        draw.line([(current_x, 0), (current_x - 40, height)], fill=alpha, width=4)
        
    return gradient.filter(ImageFilter.GaussianBlur(radius=20))

def build_advanced_boot_animation(
    logo_path="graphene_logo.png",
    screen_w=1080,   
    screen_h=1920,   
    fps=30
):
    print(f"[1/5] Инициализация проекта {screen_w}x{screen_h}...")
    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Поместите логотип в корень: {logo_path}")

    build_dir = "bootanimation_source"
    part0_dir = os.path.join(build_dir, "part0") 
    part1_dir = os.path.join(build_dir, "part1") 
    
    for d in [part0_dir, part1_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    # --- МАСШТАБИРОВАНИЕ ЛОГОТИПА (Увеличено на 15%) ---
    logo = Image.open(logo_path).convert("RGBA")
    # Базовый размер был 400, теперь он увеличен на 15% до 460 пикселей для солидного вида на экране
    target_size = 460
    logo = logo.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    logo_x = (screen_w - target_size) // 2
    logo_y = (screen_h - target_size) // 2

    logo_layer = Image.new("RGBA", (screen_w, screen_h), (0, 0, 0, 0))
    logo_layer.paste(logo, (logo_x, logo_y), logo)
    logo_mask = logo_layer.split()[-1]
    logo_glow_mask = logo_mask.filter(ImageFilter.GaussianBlur(radius=12))

    # --- ГЕНЕРАЦИЯ ЧАСТИ 0 (95 КАДРОВ) ---
    part0_frames = 95 
    print(f"[2/5] ...Генерация Части 0 ({part0_frames} кадров)")
    for i in range(part0_frames):
        frame = draw_circles_frame(screen_w, screen_h, i, part0_frames)
        frame.save(os.path.join(part0_dir, f"frame_{i:04d}.png"), "PNG")

    # --- ГЕНЕРАЦИЯ ЧАСТИ 1 (175 БАЗОВЫХ * 3 ЦИКЛА = 525 КАДРОВ) ---
    base_part1_frames = 175  
    loops_count = 3
    total_part1_frames = base_part1_frames * loops_count
    
    start_x = -800
    end_x = screen_w + 800
    step = (end_x - start_x) / base_part1_frames

    print(f"[3/5] ...Генерация Части 1 ({total_part1_frames} кадров: тройной бесшовный цикл без мигания)")
    
    global_frame_idx = 0
    for loop_idx in range(loops_count):
        for i in range(base_part1_frames):
            current_offset = int(start_x + (i * step))
            frame = Image.new("RGB", (screen_w, screen_h), (0, 0, 0))
            
            # Генерация маски блика
            shine_mask = create_slanted_soft_shine(screen_w, screen_h, current_offset, shine_width=500)
            
            # Эффект плавного проявления (Fade-In) только для первого прохода
            fade_frames = 20
            if loop_idx == 0 and i < fade_frames:
                target_base_brightness = int((i / fade_frames) * 204)
            else:
                target_base_brightness = 204 # Постоянная базовая яркость 80%
                
            base_logo_mask = ImageChops.darker(logo_mask, Image.new("L", (screen_w, screen_h), target_base_brightness))
            peak_logo_mask = ImageChops.darker(logo_mask, shine_mask)
            glow_dynamic_mask = ImageChops.darker(logo_glow_mask, ImageChops.darker(shine_mask, Image.new("L", (screen_w, screen_h), 35)))
            
            # Финальная склейка света
            final_logo_mask = ImageChops.lighter(base_logo_mask, peak_logo_mask)
            final_logo_mask = ImageChops.lighter(final_logo_mask, glow_dynamic_mask)
            
            white_color = Image.new("RGB", (screen_w, screen_h), (255, 255, 255))
            frame.paste(white_color, (0, 0), final_logo_mask)
            
            frame.save(os.path.join(part1_dir, f"frame_{global_frame_idx:04d}.png"), "PNG")
            global_frame_idx += 1

    # --- ЗАПИСЬ CONFIG И СБОРКА ZIP ---
    print("[4/5] Запись конфигурации desc.txt...")
    desc_content = f"{screen_w} {screen_h} {fps}\np 1 0 part0\np 0 0 part1\n"
    with open(os.path.join(build_dir, "desc.txt"), "w", encoding="utf-8") as f:
        f.write(desc_content)

    print("[5/5] Упаковка архива bootanimation.zip без сжатия...")
    zip_out = "bootanimation.zip"
    if os.path.exists(zip_out):
        os.remove(zip_out)

    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_STORED) as zf:
        zf.write(os.path.join(build_dir, "desc.txt"), "desc.txt")
        for folder in ["part0", "part1"]:
            folder_path = os.path.join(build_dir, folder)
            for frame in sorted(os.listdir(folder_path)):
                zf.write(os.path.join(folder_path, frame), os.path.join(folder, frame))

    shutil.rmtree(build_dir)
    print(f"\n[УСПЕХ] Финальная заставка создана: {os.path.abspath(zip_out)}")

if __name__ == "__main__":
    build_advanced_boot_animation()

