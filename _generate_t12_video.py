"""
合成 T12 8 分钟路演视频
"""
import subprocess
import os

FFMPEG = r"C:\ffmpeg\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe"
FRAMES_DIR = r"D:\shFintech\_t12_frames"
SEG_DIR = r"D:\shFintech\_t12_segments"
os.makedirs(SEG_DIR, exist_ok=True)
FPS = 30
W, H = 1920, 1080

slides = [
    'slide_01_opening.png',
    'slide_02_intro.png',
    'slide_03_pain.png',
    'slide_04_solution.png',
    'slide_05_team.png',
    'slide_06_business.png',
    'slide_07_market.png',
    'slide_08_competitive.png',
    'slide_09_financial.png',
    'slide_10_evidence.png',
    'slide_11_risk.png',
    'slide_12_ending.png',
]
DURATIONS = [40] * 12  # 12 * 40 = 480s = 8 min

for i, (slide, dur) in enumerate(zip(slides, DURATIONS)):
    src = os.path.join(FRAMES_DIR, slide)
    dst = os.path.join(SEG_DIR, slide.replace('.png', '.mp4'))
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-i", src,
        "-vf",
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fade=t=in:st=0:d=1.0,fade=t=out:st={dur-1.0}:d=1.0",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-crf", "28", "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", str(dur),
        dst
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'  {slide} 错误: {result.stderr[-200:]}')
    else:
        size_kb = os.path.getsize(dst) / 1024
        print(f'  {slide}: {size_kb:.0f} KB')

# 拼接
concat_list = os.path.join(SEG_DIR, 'concat_list.txt')
with open(concat_list, 'w', encoding='utf-8') as f:
    for slide in slides:
        f.write(f"file '{slide.replace('.png', '.mp4')}'\n")

output = 'D:/shFintech/QuantInsight_Pro_Pitch_Presenter_Video.mp4'
cmd = [
    FFMPEG, "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
    output
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f'拼接错误: {result.stderr[-300:]}')
else:
    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f'\n8 分钟路演视频: {output}')
    print(f'大小: {size_mb:.1f} MB')
