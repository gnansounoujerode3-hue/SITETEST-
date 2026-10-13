#!/usr/bin/env python3
"""
Vidéo MOTIVATION & DISCIPLINE — 100 % motion design (aucune image/photo).
Principes appliqués (MOTION-DESIGN.md, branche main) :
- une seule animation principale par écran, effets secondaires discrets
- entrées 400-650 ms, easing doux cubic-bezier(.2,.8,.2,1)
- léger décalage en cascade (stagger) des éléments secondaires
- seules la position (transform) et l'opacité sont animées
Rendu : frames Pillow 1080x1920 @30fps -> ffmpeg (binaire imageio-ffmpeg).
"""
import math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
AUDIO_DIR = os.path.join(PROJECT, "video-motivation", "audio")
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ORANGE = (255, 138, 30); WHITE = (245, 245, 250); GRAY = (110, 112, 128)
BGS = [(11,11,16),(13,16,23),(16,13,22),(11,18,24),(18,14,18),
       (13,20,17),(16,16,24),(19,15,11),(11,11,16)]

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

# ---------- utilitaires ----------
_cache = {}
def font(sz, bold=True):
    k = (sz, bold)
    if k not in _cache: _cache[k] = ImageFont.truetype(FONT_B if bold else FONT_R, sz)
    return _cache[k]

def dur_of(p):
    out = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

def bezier(x):
    """cubic-bezier(.2,.8,.2,1) — courbe douce du MOTION-DESIGN.md"""
    x = min(1.0, max(0.0, x)); lo, hi = 0.0, 1.0
    for _ in range(24):
        t = (lo+hi)/2
        bx = 3*(1-t)**2*t*0.2 + 3*(1-t)*t*t*0.2 + t**3
        lo, hi = (t, hi) if bx < x else (lo, t)
    t = (lo+hi)/2
    return 3*(1-t)**2*t*0.8 + 3*(1-t)*t*t*1.0 + t**3

def prog(lt, start, dur=0.55):            # progression easing d'un élément
    return bezier((lt-start)/dur)

def mix(c, bg, a):
    return tuple(int(bg[i] + (c[i]-bg[i])*min(1.0, max(0.0, a))) for i in range(3))

def txt(d, xy, s, fnt, color, bg, a=1.0, anchor="mm"):
    if a > 0.01: d.text(xy, s, font=fnt, fill=mix(color, bg, a), anchor=anchor)

def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

# ---------- décor + cadre commun ----------
def background(seg, gt):
    bg = BGS[seg+1]
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    ox = 26*math.sin(gt*0.45 + seg)                       # parallaxe lente (transform)
    d.ellipse([760+ox, 180, 1240+ox, 660], outline=mix((70,80,110), bg, .55), width=3)
    d.ellipse([-220-ox, 1420, 260-ox, 1900], fill=mix((38,42,62), bg, .5))
    for gx in range(72, W, 64):                            # grille de points discrète
        for gy in range(250, 1320, 64):
            d.ellipse([gx-2, gy-2, gx+2, gy+2], fill=mix(WHITE, bg, .10))
    return im, d, bg

def frame_common(d, bg, seg, gt, total):
    f = font(29)                                           # badge supérieur
    label = "MOTIVATION  •  DISCIPLINE"
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([W/2-tw/2-26, 56, W/2+tw/2+26, 118], 30,
                        fill=mix((0,0,0), bg, .55), outline=mix(WHITE, bg, .35), width=2)
    txt(d, (W/2, 88), label, f, WHITE, bg, .95)
    if 0 <= seg < 7:
        txt(d, (W-64, 88), f"{seg+1:02d}/07", font(27), WHITE, bg, .8, anchor="rm")
    d.rounded_rectangle([80, 1858, 1000, 1870], 6, fill=mix(WHITE, bg, .22))   # progression
    d.rounded_rectangle([80, 1858, 80+920*gt/total, 1870], 6, fill=ORANGE)

def subtitle(d, bg, seg, lt, scene_dur):
    """Phrase de la scène, révélée mot à mot au rythme de la voix."""
    _, _, text = SCENES[seg]
    d.rounded_rectangle([56, 1448, 1024, 1788], 28, fill=mix((0,0,0), bg, .62),
                        outline=mix(WHITE, bg, .20), width=2)
    lines = wrap(d, text, font(50), 900)
    fsize, lh = (50, 68) if len(lines) <= 4 else (42, 57)   # scènes longues : texte réduit
    if fsize == 42: lines = wrap(d, text, font(42), 920)
    voice_dur = scene_dur - PAD
    p = min(1.0, max(0.0, (lt - PAD/2) / voice_dur)) if voice_dur else 1
    total_words = sum(len(l.split()) for l in lines)
    shown = p * total_words
    y, idx = (1512 if fsize == 50 else 1498), 0
    for ln in lines:
        x = 84
        for w in ln.split():
            col = WHITE if idx < shown else GRAY
            a = 1.0 if idx < shown else .55
            txt(d, (x, y), w, font(fsize), col, bg, a, anchor="lm")
            x += d.textlength(w + " ", font=font(fsize)); idx += 1
        y += lh

def keyword(d, bg, seg, lt):
    a = prog(lt, 0.05); y = 472 - 34*(1-a)
    d.rectangle([W/2-34, y-56, W/2+34, y-46], fill=mix(ORANGE, bg, a))
    txt(d, (W/2, y), SCENES[seg][1], font(42), ORANGE, bg, a)

# ---------- animations principales (1 par écran) ----------
def main_anim(d, bg, seg, lt, dur):
    cx = W/2
    if seg == 0:   # COMMENCER -> CONTINUER : flèche qui se dessine
        a = prog(lt, .25); txt(d, (cx, 700-36*(1-a)), "COMMENCER", font(78), WHITE, bg, a)
        p = prog(lt, .85, .7)
        if p > 0:
            x2 = 250 + (830-250)*p
            d.line([250, 812, x2, 812], fill=ORANGE, width=11)
            if p > .85: d.polygon([(x2, 788), (x2, 836), (x2+42, 812)], fill=ORANGE)
        a = prog(lt, 1.55, .5); s = int(94*(0.82+0.18*a))
        txt(d, (cx, 958), "CONTINUER", font(s), ORANGE, bg, a)
    elif seg == 1: # HUMEUR (instable) vs DÉCISION (verrouillée)
        for i, (t1, t2, hot) in enumerate([("MOTIVATION", "HUMEUR", False),
                                           ("DISCIPLINE", "DÉCISION", True)]):
            y = 640 + i*268; a = prog(lt, .25+i*.45)
            xoff = -46*(1-a)
            col = ORANGE if hot else GRAY
            d.rounded_rectangle([140+xoff, y, 940+xoff, y+212], 26,
                                fill=mix((24,26,38), bg, a), outline=mix(col, bg, .9*a), width=3)
            txt(d, (176+xoff, y+48), t1, font(30), GRAY, bg, a*.95, anchor="lm")
            txt(d, (176+xoff, y+128), t2, font(72), WHITE if hot else (200,200,210), bg, a, anchor="lm")
            if not hot:
                pts = [(190+xoff+gx, y+178+13*math.sin(gx*.028+lt*5)) for gx in range(0, 640, 16)]
                d.line(pts, fill=mix((150,155,175), bg, .55+.25*math.sin(lt*3)), width=5)
            elif lt > 2.0:
                p = prog(lt, 2.0, .45); ccx, ccy = 842+xoff, y+106
                d.ellipse([ccx-46, ccy-46, ccx+46, ccy+46], outline=mix(ORANGE, bg, p), width=7)
                if p > .4:
                    q = (p-.4)/.6
                    d.line([ccx-22, ccy, ccx-22+18*q, ccy+16*q], fill=mix(WHITE, bg, q), width=8)
                    if q > .5: d.line([ccx-4, ccy+16, ccx-4+30*(q-.5)*2, ccy+16-34*(q-.5)*2],
                                      fill=mix(WHITE, bg, q), width=8)
    elif seg == 2: # Lever de soleil géométrique + 05:00
        a = prog(lt, .2); txt(d, (cx, 568), "05:00", font(112), WHITE, bg, a)
        p = prog(lt, .9, dur*.62)
        sy = 1092 - 205*p
        for k in range(8):
            ang = k*math.pi/4 + lt*.12; r1, r2 = 168, 208
            d.line([cx+r1*math.cos(ang), sy+r1*math.sin(ang),
                    cx+r2*math.cos(ang), sy+r2*math.sin(ang)], fill=mix(ORANGE, bg, .85*p), width=9)
        d.ellipse([cx-128, sy-128, cx+128, sy+128], fill=mix(ORANGE, bg, .96))
        d.rectangle([0, 1093, W, 1420], fill=bg)
        d.line([120, 1092, 960, 1092], fill=mix(WHITE, bg, .9), width=5)
        a = prog(lt, 2.2); txt(d, (cx, 1212-26*(1-a)), "TU TE RELÈVES", font(64), WHITE, bg, a)
    elif seg == 3: # Les manques barrés, puis l'essentiel
        for i, s in enumerate(["SANS ENVIE", "SANS ÉNERGIE", "SANS APPLAUDISSEMENTS"]):
            y = 606 + i*138; a = prog(lt, .3+i*.35); xoff = -40*(1-a)
            d.rounded_rectangle([172+xoff, y, 908+xoff, y+98], 49, fill=mix((26,26,36), bg, a),
                                outline=mix(GRAY, bg, .7*a), width=2)
            txt(d, (cx+xoff, y+50), s, font(42), (185,187,200), bg, a*(.55 if lt > 1.6+i*.35 else 1))
            sp = prog(lt, 1.6+i*.35, .4)
            if sp > 0: d.line([196+xoff, y+50, 196+xoff+(688)*sp, y+50], fill=mix(ORANGE, bg, .95), width=9)
        a = prog(lt, 3.0, .5); s = int(74*(0.82+0.18*a))
        txt(d, (cx, 1078), "CES JOURS-LÀ", font(s), WHITE, bg, a)
        txt(d, (cx, 1174), "COMPTENT LE PLUS", font(s), ORANGE, bg, a)
    elif seg == 4: # Calendrier : la régularité se remplit jour après jour
        a = prog(lt, .2); txt(d, (cx, 566-30*(1-a)), "RÉGULIER > PARFAIT", font(66), WHITE, bg, a)
        n = min(21, max(0, int((lt-1.0)/0.115)))
        for i in range(21):
            r, c = divmod(i, 7); x, y = 212+c*110, 700+r*118
            if i < n:
                pop = 1.0 if i < n-1 else .72+.28*prog(lt, 1.0+i*.115, .3)
                s = 44*pop
                d.rounded_rectangle([x-s, y-s, x+s, y+s], 20, fill=mix(ORANGE, bg, .35+.65*pop))
                d.line([x-18, y, x-6, y+14], fill=mix((20,14,8), bg, pop), width=8)
                d.line([x-6, y+14, x+20, y-16], fill=mix((20,14,8), bg, pop), width=8)
            else:
                d.rounded_rectangle([x-44, y-44, x+44, y+44], 20, outline=mix(GRAY, bg, .55), width=3)
        a = prog(lt, 1.4); txt(d, (cx, 1130), "1 JOUR APRÈS L'AUTRE", font(46), ORANGE, bg, a)
    elif seg == 5: # Escaliers : petits pas répétés
        a = prog(lt, .2)
        txt(d, (cx, 548-30*(1-a)), "PETITS PAS", font(76), WHITE, bg, a)
        txt(d, (cx, 640-30*(1-a)), "RÉPÉTÉS", font(76), ORANGE, bg, a)
        base, sw, sh = 1205, 128, 57
        for i in range(6):
            ap = prog(lt, .7+i*.13, .4); x, top = 148+i*sw, base-(i+1)*sh
            d.rectangle([x, top+sh*(1-ap), x+sw-10, base], fill=mix((30,34,52), bg, .95))
            d.rectangle([x, top+sh*(1-ap), x+sw-10, top+sh*(1-ap)+9], fill=mix(ORANGE, bg, .95*ap))
        cp = min(1.0, max(0.0, (lt-1.8)/(dur-2.6))) if dur > 2.6 else 1
        step = min(5.999, cp*6); si, fr = int(step), step-int(step)
        bx = 148+si*sw+sw/2 + fr*sw
        by = base-(si+1)*sh-26 - math.sin(fr*math.pi)*34 - fr*sh
        d.ellipse([bx-25, by-25, bx+25, by+25], fill=ORANGE)
        if cp >= .99:
            p = prog(lt, 1.8+(dur-2.6), .5)
            d.ellipse([858-52*p, 742-52*p, 858+52*p, 742+52*p], outline=mix(ORANGE, bg, p), width=8)
    elif seg == 6: # EXCUSES barré, puis RELÈVE-TOI / AVANCE
        a = prog(lt, .25); txt(d, (cx, 682), "EXCUSES", font(98), GRAY, bg, .55+.45*a)
        p = prog(lt, .95, .55)
        if p > 0: d.line([168, 682, 168+(744)*p, 682], fill=ORANGE, width=15)
        for i, (s, col) in enumerate([("RELÈVE-TOI", WHITE), ("AVANCE.", ORANGE)]):
            a = prog(lt, 1.85+i*.28); y = 906+i*112 - 38*(1-a)
            txt(d, (cx, y), s, font(int(88*(0.85+0.15*a))), col, bg, a)
        p = prog(lt, 2.7, .6)
        if p > 0:
            x2 = 340+400*p; d.line([340, 1172, x2, 1172], fill=mix(ORANGE, bg, .9), width=10)
            if p > .8: d.polygon([(x2, 1150), (x2, 1194), (x2+38, 1172)], fill=ORANGE)

def intro_outro(d, bg, kind, lt):
    cx = W/2
    if kind == "intro":
        p = prog(lt, 0, 1.1); r = 90+250*p
        d.ellipse([cx-r, 872-r, cx+r, 872+r], outline=mix(ORANGE, bg, .35*(1-p*.4)), width=4)
        for i, (s, col) in enumerate([("MOTIVATION", WHITE), ("& DISCIPLINE", ORANGE)]):
            a = prog(lt, .15+i*.14); txt(d, (cx, 818+i*112-40*(1-a)), s, font(94), col, bg, a)
        p = prog(lt, .75, .55); hw = 152*p
        d.rectangle([cx-hw, 972, cx+hw, 982], fill=mix(ORANGE, bg, p))
        a = prog(lt, 1.15); txt(d, (cx, 1058), "Ne négocie pas avec tes excuses.", font(40, False), WHITE, bg, a)
    else:
        p = prog(lt, 0, 1.5)
        d.arc([cx-235, 585, cx+235, 1055], start=-90, end=-90+360*p, fill=ORANGE, width=12)
        if p > .92:
            q = prog(lt, 1.45, .4)
            d.line([cx-88, 822, cx-88+62*q, 822+58*q], fill=mix(WHITE, bg, q), width=15)
            if q > .5: d.line([cx-26, 880, cx-26+128*(q-.5)*2, 880-118*(q-.5)*2], fill=mix(WHITE, bg, q), width=15)
        for i, (s, col) in enumerate([("DISCIPLINE.", ORANGE), ("CHAQUE JOUR.", WHITE)]):
            a = prog(lt, .5+i*.16); txt(d, (cx, 1152+i*104-36*(1-a)), s, font(86), col, bg, a)
        a = prog(lt, 1.3); txt(d, (cx, 1372), "Commence aujourd'hui.", font(44, False), WHITE, bg, a)

# ---------- assemblage ----------
def fmt_srt(s):
    ms = int((s % 1)*1000); s = int(s)
    return f"{s//3600:02d}:{s//60%60:02d}:{s%60:02d},{ms:03d}"

def main():
    durs = [dur_of(os.path.join(AUDIO_DIR, f"{n}.mp3")) for n, _, _ in SCENES]
    scene_durs = [d+PAD for d in durs]
    total = INTRO_DUR + sum(scene_durs) + OUTRO_DUR
    starts, t = [], INTRO_DUR
    for d in scene_durs: starts.append(t); t += d
    print(f"Scènes: {[round(x,2) for x in scene_durs]} | Total {total:.1f}s")

    sys.path.insert(0, os.path.join(PROJECT, "video-motivation"))
    import build_video as bv
    music = os.path.join(ROOT, "music.wav"); bv.make_music(total, music)

    # piste voix synchronisée
    cmd = [FF, "-y"]
    for n, _, _ in SCENES: cmd += ["-i", os.path.join(AUDIO_DIR, f"{n}.mp3")]
    fc = "".join(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,adelay={int((starts[i]+PAD/2)*1000)}|{int((starts[i]+PAD/2)*1000)}[a{i}];" for i in range(7))
    fc += "".join(f"[a{i}]" for i in range(7)) + f"amix=inputs=7:duration=longest:normalize=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f},asetpts=N/SR/TB[out]"
    voice = os.path.join(ROOT, "voice.wav")
    subprocess.run(cmd + ["-filter_complex", fc, "-map", "[out]", voice],
                   check=True, capture_output=True, text=True)

    # rendu des frames -> vidéo muette
    silent = os.path.join(ROOT, "motion-silent.mp4")
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    nframes = int(total*FPS)
    for fi in range(nframes):
        gt = fi/FPS
        if gt < INTRO_DUR: seg, lt, sd = -1, gt, INTRO_DUR
        elif gt >= total-OUTRO_DUR: seg, lt, sd = 7, gt-(total-OUTRO_DUR), OUTRO_DUR
        else:
            seg = next(i for i in range(7) if starts[i] <= gt < starts[i]+scene_durs[i])
            lt, sd = gt-starts[seg], scene_durs[seg]
        im, d, bg = background(seg, gt)
        if seg == -1: intro_outro(d, bg, "intro", lt)
        elif seg == 7: intro_outro(d, bg, "outro", lt)
        else:
            keyword(d, bg, seg, lt); main_anim(d, bg, seg, lt, sd); subtitle(d, bg, seg, lt, sd)
        frame_common(d, bg, seg, gt, total)
        fade = min(1.0, lt/0.4, (sd-lt)/0.45)              # fondus transform+opacité
        if fade < 1: im = Image.blend(Image.new("RGB", (W, H), bg), im, max(0.0, fade))
        proc.stdin.write(im.tobytes())
        if fi % 150 == 0: print(f"frame {fi}/{nframes}")
    proc.stdin.close(); proc.wait()

    final = os.path.join(PROJECT, "motivation-discipline-motion-design.mp4")
    fc2 = "[0:a]volume=1.0[voice];[1:a]volume=0.16[mus];[voice][mus]amix=inputs=2:duration=first:normalize=0[aout]"
    subprocess.run([FF, "-y", "-i", silent, "-i", voice, "-i", music, "-filter_complex",
                    "[1:a]volume=1.0[voice];[2:a]volume=0.16[mus];[voice][mus]amix=inputs=2:duration=first:normalize=0[aout]",
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", final],
                   check=True, capture_output=True, text=True)

    cover = os.path.join(PROJECT, "motivation-discipline-motion-design-cover.jpg")
    subprocess.run([FF, "-y", "-ss", f"{total-1.2:.2f}", "-i", final, "-frames:v", "1", "-q:v", "2", cover],
                   check=True, capture_output=True, text=True)
    srt, t = [], INTRO_DUR
    for i, (_, _, text) in enumerate(SCENES):
        srt.append(f"{i+1}\n{fmt_srt(t)} --> {fmt_srt(t+scene_durs[i])}\n{text}\n"); t += scene_durs[i]
    with open(os.path.join(PROJECT, "motivation-discipline-motion-design.srt"), "w") as f: f.write("\n".join(srt))
    with open(os.path.join(ROOT, "script.txt"), "w") as f:
        f.write("MOTIVATION & DISCIPLINE — version 100% motion design\n\n" +
                "\n".join(f"{i+1}. {t}" for i, (_, _, t) in enumerate(SCENES)))
    for tmp in (music, voice, silent): os.remove(tmp)
    print("OK →", final)

if __name__ == "__main__":
    main()
