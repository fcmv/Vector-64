"""Add restrained title and technical overlays to a real Vector Scope recording."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FPS = 60


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def opacity(start: float, end: float, fade: float) -> str:
    return (f"if(lt(t,{start}),0,if(lt(t,{start + fade}),(t-{start})/{fade},"
            f"if(lt(t,{end - fade}),1,if(lt(t,{end}),({end}-t)/{fade},0))))")


def backing(name: str, seconds: float, start: float, end: float, fade: float,
            width: int, height: int, alpha: float) -> str:
    return (
        f"color=c=black@{alpha}:s={width}x{height}:r={FPS}:d={seconds},format=rgba,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=0x41444c:t=1,"
        f"fade=t=in:st={start}:d={fade}:alpha=1,fade=t=out:st={end - fade}:d={fade}:alpha=1[{name}]"
    )


def overlays(seconds: float, playback_start: float, architecture_start: float, architecture_seconds: float) -> str:
    architecture_end = architecture_start + architecture_seconds
    roadmap_start = seconds - 4
    title_end = playback_start + 1.6
    title_alpha = opacity(0.25, title_end, 1.2)
    architecture_alpha = opacity(architecture_start, architecture_end, 0.65)
    roadmap_alpha = opacity(roadmap_start, seconds - 0.15, 0.45)
    filters = [
        "drawbox=x=20:y=22:w=430:h=30:color=0x111214:t=fill",
        "drawtext=fontfile=regular.ttf:textfile=brand.txt:fontsize=23:fontcolor=0xc7cbd1:x=28:y=27",
    ]
    for phase in range(4):
        # Punctuation spaces reserve each dot's advance, so the title never shifts.
        filters.append(
            f"drawtext=fontfile=title.ttf:textfile=title-{phase}.txt:fontsize=84:fontcolor=0xf1f0f4:"
            "borderw=1:bordercolor=black@0.8:shadowcolor=black@0.9:shadowy=3:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:alpha='{title_alpha}':"
            f"enable='between(mod(max(t-0.25,0),1.8),{phase * 0.45:.2f},{(phase + 1) * 0.45 - 0.000001:.6f})'"
        )
    for label, size, y in (("architecture-name", 64, 390), ("architecture-features", 44, 484),
                           ("architecture-layers", 54, 559), ("architecture-output", 46, 638)):
        filters.append(
            f"drawtext=fontfile=regular.ttf:textfile={label}.txt:fontsize={size}:fontcolor=0xf3f4f6:"
            f"x=(w-text_w)/2:y={y}:alpha='{architecture_alpha}'"
        )
    filters.append(
        "drawtext=fontfile=regular.ttf:textfile=roadmap.txt:fontsize=34:line_spacing=16:"
        f"fontcolor=0xf3f4f6:x=(w-text_w)/2:y=880:alpha='{roadmap_alpha}'"
    )
    panels = [
        backing("architecture_bg", seconds, architecture_start, architecture_end, 0.65, 1360, 420, 1.0),
        backing("roadmap_bg", seconds, roadmap_start, seconds - 0.15, 0.45, 1440, 160, 0.97),
    ]
    composite = (
        "[base][architecture_bg]overlay=280:330:shortest=1[explained];"
        "[explained][roadmap_bg]overlay=240:840:shortest=1[backed];"
        f"[backed]{','.join(filters)}[out]"
    )
    return ";".join([*panels, composite])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "docs/assets/vector-scope-live-1080p.mp4")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/assets/it-thinks-1080p.mp4")
    parser.add_argument("--raw-output", type=Path, help="also save a normalized, uncaptioned source clip")
    parser.add_argument("--start", type=float, default=4.0)
    parser.add_argument("--seconds", type=float, default=100.0)
    parser.add_argument("--playback-start", type=float, default=8.7, help="play resumes here in the source recording")
    parser.add_argument("--architecture-start", type=float, default=46.5,
                        help="source timestamp when the enlarged board closes and the network takes focus")
    parser.add_argument("--architecture-seconds", type=float, default=7.0)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--title-font", type=Path)
    args = parser.parse_args()
    source, output = args.input.resolve(strict=True), args.output.resolve()
    raw_output = args.raw_output.resolve() if args.raw_output else None
    if source == output or raw_output in (source, output):
        parser.error("input, output and raw output must differ")
    if args.start < 0 or args.seconds < 20 or not args.start < args.playback_start < args.start + args.seconds - 12:
        parser.error("require a nonnegative start, at least 20 seconds and playback before the closing overlays")
    if (args.architecture_start < args.playback_start or args.architecture_seconds <= 1.3
            or args.architecture_start + args.architecture_seconds > args.start + args.seconds - 4):
        parser.error("architecture must follow playback and finish before the roadmap overlay")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        parser.error("ffmpeg and ffprobe must be installed")
    regular = args.font or next((p for p in (Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")) if p.is_file()), None)
    title_font = args.title_font or next((p for p in (Path("C:/Windows/Fonts/segoeuisl.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")) if p.is_file()), None)
    if regular is None or title_font is None:
        parser.error("supply --font and --title-font")
    probe = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-show_streams", "-show_format",
                                               "-of", "json", str(source)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    if ((video["width"], video["height"]) != (1920, 1080)
            or float(video.get("duration", probe["format"]["duration"])) < args.start + args.seconds
            or Fraction(video["avg_frame_rate"]) < 30):
        parser.error("source must be 1920x1080, at least 30 fps and cover the selected interval")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vector64-showcase-") as directory:
        work = Path(directory)
        shutil.copyfile(regular, work / "regular.ttf")
        shutil.copyfile(title_font, work / "title.ttf")
        texts = {
            "brand": "fcmv/vector-64",
            "title": "It's thinking ...",
            "architecture-name": "STK-HalfKA NNUE",
            "architecture-features": "22,528 features per perspective | 2 x 1024 accumulators",
            "architecture-layers": "Pairwise > 1024 > 16 > 32 > 1",
            "architecture-output": "8 output buckets + PSQT",
            "roadmap": "Next: engine correctness, reproducible training and search.\n"
                       "ROADMAP.md | fcmv/vector-64",
        }
        for phase in range(4):
            texts[f"title-{phase}"] = "It's thinking" + "." * phase + "\u2008" * (3 - phase)
        for name, text in texts.items():
            (work / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
        encoder = ["-an", "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-threads", "2",
                   "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        overlay_filters = overlays(args.seconds, args.playback_start - args.start,
                                   args.architecture_start - args.start, args.architecture_seconds)
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(args.start), "-i", str(source),
            "-filter_complex", f"[0:v]setpts=PTS-STARTPTS,fps={FPS},setsar=1[base];{overlay_filters}",
            "-map", "[out]", "-filter_complex_threads", "1", "-t", str(args.seconds), *encoder, str(output),
        ], cwd=work, check=True)
        if raw_output:
            raw_output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                "-vf", f"setpts=PTS-STARTPTS,fps={FPS},setsar=1", "-t", str(args.start + args.seconds),
                *encoder, str(raw_output),
            ], check=True)
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", "2", "-i", str(output),
                        "-frames:v", "1", str(output.with_suffix(".png"))], check=True)
    manifest = {
        "source_sha256": sha256(source), "output_sha256": sha256(output),
        "raw_output_sha256": sha256(raw_output) if raw_output else None,
        "width": 1920, "height": 1080, "fps": FPS, "seconds": args.seconds, "audio": False,
        "source": "user-provided Microsoft Game DVR window recording",
        "source_average_fps": video["avg_frame_rate"],
        "source_start_seconds": args.start, "source_end_seconds": args.start + args.seconds,
        "source_playback_start_seconds": args.playback_start,
        "editing": "continuous recording; centered animated title; architecture as the board closes; roadmap ending",
        "frame_pacing": "60 fps constant output; source frames may repeat; no motion interpolation",
        "branding": texts["brand"], "title": texts["title"],
        "overlays": [
            {"name": "title", "start": 0.25, "end": round(args.playback_start - args.start + 1.6, 3),
             "position": "screen center", "typography": "84px Segoe UI Semilight or supplied title font",
             "backing": None,
             "ellipsis": "0 to 3 dots, 450ms per step, fixed punctuation-space advances"},
            {"name": "architecture", "start": args.architecture_start - args.start,
             "end": args.architecture_start - args.start + args.architecture_seconds,
             "position": "screen center", "backing": "1360x420 opaque black panel, matched fades",
             "font_sizes_px": [64, 44, 54, 46], "font": "regular body font",
             "text": "\n".join(texts[f"architecture-{name}"]
                                                               for name in ("name", "features", "layers", "output"))},
            {"name": "roadmap", "start": args.seconds - 4, "end": args.seconds - 0.15,
             "text": texts["roadmap"]},
        ],
    }
    output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
