"""
合成 3 条 T11 技术短视频
"""
import subprocess
import os

FFMPEG = r"C:\ffmpeg\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe"
FRAMES_DIR = r"D:\shFintech\_t11_frames"
SEG_DIR = r"D:\shFintech\_t11_segments"
os.makedirs(SEG_DIR, exist_ok=True)
FPS = 30
W, H = 1920, 1080

# 3 个视频的 7 个场景（每个 13s = 90s 总时长）
videos = {
    'v1_ai_qa': [f'v1_{i:02d}_{name}.png' for i, name in zip(range(1, 8), ['title','question','thinking','answer','followup','metrics','ending'])],
    'v2_backtest': [f'v2_{i:02d}_{name}.png' for i, name in zip(range(1, 8), ['title','strategies','code','results','attribution','rigor','ending'])],
    'v3_alt_data': [f'v3_{i:02d}_{name}.png' for i, name in zip(range(1, 8), ['title','satellite','sentiment','supply_chain','dashboard','cases','ending'])],
}

DURATIONS = [13, 13, 13, 13, 13, 13, 12]  # 7 场景: 13+13+13+13+13+13+12 = 90s

# 生成每段视频
for vid_name, frames in videos.items():
    print(f'\n=== {vid_name} ===')
    for i, (frame, dur) in enumerate(zip(frames, DURATIONS)):
        src = os.path.join(FRAMES_DIR, frame)
        dst = os.path.join(SEG_DIR, frame.replace('.png', '.mp4'))
        fade_in = min(0.5, dur / 3)
        fade_out_start = max(0, dur - 0.5)
        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-i", src,
            "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fade=t=in:st=0:d={fade_in},fade=t=out:st={fade_out_start}:d=0.5",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-r", str(FPS),
            "-t", str(dur),
            dst
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f'  {frame} 错误: {result.stderr[-200:]}')
        else:
            size_kb = os.path.getsize(dst) / 1024
            print(f'  {frame}: {size_kb:.0f} KB')

# 拼接为完整视频
for vid_name, frames in videos.items():
    concat_list = os.path.join(SEG_DIR, f'{vid_name}_list.txt')
    with open(concat_list, 'w', encoding='utf-8') as f:
        for frame in frames:
            f.write(f"file '{frame.replace('.png', '.mp4')}'\n")
    output = f'D:/shFintech/QuantInsight_Pro_Tech_Video_{vid_name}.mp4'
    print(f'\n拼接 {vid_name} -> {output}')
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
        output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'  错误: {result.stderr[-300:]}')
    else:
        size_mb = os.path.getsize(output) / 1024 / 1024
        print(f'  完成: {size_mb:.1f} MB')

print('\n=== 3 条 T11 短视频生成完成 ===')
