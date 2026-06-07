"""
简化版：静态帧 + 短淡入淡出，快速生成视频片段
"""
import subprocess
import os

FFMPEG = r"C:\ffmpeg\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe"
FRAMES_DIR = r"D:\shFintech\_video_frames"
SEGMENTS_DIR = r"D:\shFintech\_video_segments"
os.makedirs(SEGMENTS_DIR, exist_ok=True)

scenes = [
    ("scene_01_cover.png", 15, 0),
    ("scene_02_ai_qa.png", 30, 15),
    ("scene_03_alt_data.png", 30, 45),
    ("scene_04_backtest.png", 30, 75),
    ("scene_05_financial.png", 15, 105),
    ("scene_06_market.png", 20, 120),
    ("scene_07_team.png", 10, 140),
    ("scene_08_business.png", 20, 150),
    ("scene_09_ending.png", 10, 170),
]
FPS = 30
W, H = 1920, 1080

for filename, duration, start_sec in scenes:
    src = os.path.join(FRAMES_DIR, filename)
    dst = os.path.join(SEGMENTS_DIR, filename.replace('.png', '.mp4'))

    if os.path.exists(dst) and os.path.getsize(dst) > 10000:
        print(f'跳过 {filename} (已存在)')
        continue

    print(f'生成 {filename} -> {duration}s ...')
    # 静态帧 + 淡入淡出
    fade_in = min(1.0, duration / 2)
    fade_out_start = max(0, duration - 1.0)
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-i", src,
        "-vf",
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fade=t=in:st=0:d={fade_in},fade=t=out:st={fade_out_start}:d=1.0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-t", str(duration),
        dst
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'  错误: {result.stderr[-300:]}')
    else:
        size_kb = os.path.getsize(dst) / 1024
        print(f'  完成 ({size_kb:.0f} KB)')

print('\n所有片段生成完成')
