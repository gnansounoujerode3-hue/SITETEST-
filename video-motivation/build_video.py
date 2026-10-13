#!/usr/bin/env python3
"""Assemble la vidéo verticale Motivation & Discipline (1080x1920)."""
import math, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ORANGE = (255, 138, 30)
WHITE = (255, 255, 255)

SCENES = [
    ("scene1", "COMMENCER → CONTINUER",
     "La motivation te fait commencer, mais c'est la discipline qui te fait continuer."),
    ("scene2", "HUMEUR  vs  DÉCISION",
     "La motivation dépend de ton humeur. La discipline, elle, dépend de ta décision."),
    ("scene3", "CHAQUE MATIN, TU TE RELÈVES",
     "Chaque matin où tu te lèves quand tu n'en as pas envie, tu construis la personne que tu veux devenir."),
    ("scene4", "LES JOURS SANS ENVIE",
     "Il y aura des jours sans envie, sans énergie, sans applaudissements. C'est précisément ces jours-là qui comptent le plus."),
    ("scene5", "RÉGULARITÉ > PERFECTION",
     "Tu n'as pas besoin d'être parfait. Tu dois juste être régulier, un jour après l'autre."),
    ("scene6", "PETITS PAS, CHAQUE JOUR",
     "Les résultats ne viennent pas d'un grand effort une fois, mais de petits pas répétés chaque jour."),
    ("scene7", "AUCUNE EXCUSE",
     "Alors relève-toi, avance, et ne négocie pas avec tes excuses. Ton futur te regarde."),
]
INTRO_DUR, OUTRO_DUR, PAD = 2.2, 2.8, 0.70

def dur_of(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def gradient(overlay, y0, y1, max_alpha, reverse=False):
    d = ImageDraw.Draw(overlay)
    for y in range(y0, y1):
        p = (y - y0) / max(1, (y1 - y0))
        a = int(max_alpha * (1-p if reverse else p))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))

def make_overlay(idx, keyword, text):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gradient(ov, 1250, H, 215); gradient(ov, 0, 260, 140, reverse=True)
    d = ImageDraw.Draw(ov)
    # top pill
    label = "MOTIVATION  •  DISCIPLINE"
    f = font(30)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([(W/2-tw/2-28, 58), (W/2+tw/2+28, 122)], 30, fill=(0,0,0,140), outline=(255,255,255,70), width=2)
    d.text((W/2, 90), label, font=f, fill=WHITE, anchor="mm")
    d.text((W-70, 90), f"{idx+1:02d}/07", font=font(28), fill=(255,255,255,180), anchor="rm")
    # keyword + subtitle
    d.rectangle([(80, 1312), (150, 1322)], fill=ORANGE)
    d.text((80, 1350), keyword, font=font(46), fill=ORANGE)
    lines = wrap(d, text, font(56), 920)
    y = 1435
    for ln in lines:
        d.text((82, y+3), ln, font=font(56), fill=(0,0,0,200))
        d.text((80, y), ln, font=font(56), fill=WHITE)
        y += 72
    # progress bar
    d.rounded_rectangle([(80, 1862), (1000, 1872)], 5, fill=(255,255,255,70))
    d.rounded_rectangle([(80, 1862), (80 + 920*(idx+1)/7, 1872)], 5, fill=ORANGE)
    p = os.path.join(ROOT, "overlays", f"scene{idx+1}.png"); ov.save(p); return p

def make_card(kind):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gradient(ov, 0, H, 90)
    d = ImageDraw.Draw(ov)
    if kind == "intro":
        d.text((W/2, 800), "MOTIVATION", font=font(96), fill=WHITE, anchor="mm")
        d.text((W/2, 910), "& DISCIPLINE", font=font(96), fill=ORANGE, anchor="mm")
        d.rectangle([(390, 985), (690, 995)], fill=ORANGE)
        d.text((W/2, 1060), "Ne négocie pas avec tes excuses.", font=font(40, False), fill=WHITE, anchor="mm")
    else:
        d.text((W/2, 810), "DISCIPLINE.", font=font(92), fill=ORANGE, anchor="mm")
        d.text((W/2, 920), "CHAQUE JOUR.", font=font(92), fill=WHITE, anchor="mm")
        d.text((W/2, 1030), "Commence aujourd'hui.", font=font(44, False), fill=WHITE, anchor="mm")
    p = os.path.join(ROOT, "overlays", f"{kind}.png"); ov.save(p); return p

def make_music(total, path):
    sr, t = 44100, np.arange(int(total*44100))/44100
    chords = [  # Am - F - C - G (fréquences fondamentales des accords)
        [110.00, 130.81, 164.81, 220.00], [87.31, 110.00, 130.81, 174.61],
        [130.81, 164.81, 196.00, 261.63], [98.00, 123.47, 146.83, 196.00]]
    music = np.zeros_like(t)
    chord_dur = 4.0
    for i, freqs in enumerate(chords * math.ceil(total/chord_dur/4 + 1)):
        start = i*chord_dur
        if start >= total: break
        m = (t >= start-0.6) & (t < start+chord_dur+0.6)
        env = np.clip((t[m]-start+0.6)/1.2, 0, 1) * np.clip((start+chord_dur+0.6-t[m])/1.2, 0, 1)
        seg = sum(np.sin(2*np.pi*f*t[m]) + 0.35*np.sin(2*np.pi*f*2*t[m]) for f in freqs)
        music[m] += seg * env * 0.055
        # arpège doux (notes de l'accord, octave supérieure)
        for k in range(8):
            nt = start + k*0.5
            mm = (t >= nt) & (t < nt+1.2)
            if mm.any():
                f = freqs[k % len(freqs)]*2
                music[mm] += np.sin(2*np.pi*f*t[mm]) * np.exp(-(t[mm]-nt)*2.2) * 0.045
    music *= (0.75 + 0.25*np.clip((t-(total-12))/12, 0, 1))            # montée finale
    music *= np.minimum(1, t/1.0) * np.minimum(1, np.clip((total-t)/3, 0, 1))  # fondus
    stereo = np.stack([music, music], axis=1)
    pcm = (np.clip(stereo, -1, 1)*32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

def segment(img, overlay, audio, dur, out, zoom_in=True):
    frames = max(1, int(dur*30))
    z = (f"min(1+0.12*on/{frames},1.12)" if zoom_in else f"max(1.12-0.12*on/{frames},1.0)")
    fc = (f"[0:v]scale=1440:2560:force_original_aspect_ratio=increase,crop=1440:2560,"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
          f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.45:.2f}:d=0.45,format=yuv420p[bg];"
          f"[bg][1:v]overlay=0:0[v];"
          f"[2:a]aresample=48000,atrim=0:{dur:.3f},asetpts=N/SR/TB[a]")
    cmd = [FF, "-y", "-i", img, "-i", overlay]
    cmd += (["-i", audio] if audio else ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"])
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
            "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", out]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

def fmt_srt(s):
    ms = int((s % 1)*1000); s = int(s)
    return f"{s//3600:02d}:{s//60%60:02d}:{s%60:02d},{ms:03d}"

def main():
    os.makedirs(os.path.join(ROOT, "overlays"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "segments"), exist_ok=True)
    durs = [dur_of(os.path.join(ROOT, "audio", f"{n}.mp3")) for n, _, _ in SCENES]
    scene_durs = [d + PAD for d in durs]
    total = INTRO_DUR + sum(scene_durs) + OUTRO_DUR
    print(f"Durées scènes: {[round(x,2) for x in scene_durs]} | Total: {total:.1f}s")

    make_music(total, os.path.join(ROOT, "music.wav"))
    overlays = [make_overlay(i, k, t) for i, (_, k, t) in enumerate(SCENES)]
    intro_ov, outro_ov = make_card("intro"), make_card("outro")

    segs = []
    def add(img, ov, audio, dur, name, zin):
        out = os.path.join(ROOT, "segments", name)
        print("→", name); segment(img, ov, audio, dur, out, zin); segs.append(out)
    img = lambda n: os.path.join(ROOT, "images", f"{n}.jpg")
    add(img("scene1"), intro_ov, None, INTRO_DUR, "00-intro.mp4", True)
    for i, (name, _, _) in enumerate(SCENES):
        # voix décalée de 0,35 s dans le segment : ré-encoder avec adelay via fichier pré-décalé
        add(img(name), overlays[i], os.path.join(ROOT, "audio", f"{name}.mp3"),
            scene_durs[i], f"{i+1:02d}-{name}.mp4", zin=(i % 2 == 0))
    add(img("scene7"), outro_ov, None, OUTRO_DUR, "08-outro.mp4", True)

    lst = os.path.join(ROOT, "segments", "list.txt")
    with open(lst, "w") as f:
        for s in segs: f.write(f"file '{s}'\n")
    concat = os.path.join(ROOT, "concat.mp4")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", concat],
                   check=True, capture_output=True, text=True)

    final = os.path.join(os.path.dirname(ROOT), "motivation-discipline.mp4")
    fc = ("[0:a]volume=1.0[voice];[1:a]volume=0.16[mus];"
          "[voice][mus]amix=inputs=2:duration=first:normalize=0[aout]")
    subprocess.run([FF, "-y", "-i", concat, "-i", os.path.join(ROOT, "music.wav"),
                    "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", final], check=True, capture_output=True, text=True)

    # SRT + script
    t, srt = INTRO_DUR, []
    for i, (_, _, text) in enumerate(SCENES):
        srt.append(f"{i+1}\n{fmt_srt(t)} --> {fmt_srt(t+scene_durs[i])}\n{text}\n"); t += scene_durs[i]
    with open(os.path.join(os.path.dirname(ROOT), "motivation-discipline.srt"), "w") as f: f.write("\n".join(srt))
    with open(os.path.join(ROOT, "script.txt"), "w") as f:
        f.write("MOTIVATION & DISCIPLINE — script\n\n" + "\n".join(f"{i+1}. {t}" for i, (_, _, t) in enumerate(SCENES)))
    print("OK →", final)

if __name__ == "__main__":
    main()
