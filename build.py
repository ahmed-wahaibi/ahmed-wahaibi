"""Builds card.svg: a joker ASCII portrait plus neofetch-style profile stats.

Run: GH_TOKEN=... python build.py   (needs Pillow)
"""
import datetime as dt
import json
import math
import os
import random
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter

USER = "ahmed-wahaibi"

INFO = [  # (key, value); None = section header
    ("OS", "Ahmed Al Wahaibi"),
    ("Host", "Rihal, Muscat, OM"),
    ("Kernel", "Senior Software Engineer"),
    ("Environment", "VSCode, Vim"),
    ("Tools", "Git, Docker, Figma, Blender"),
    ("Languages.Programming", "Go, Python, TypeScript, SQL"),
    ("Languages.Real", "Arabic, English"),
    ("Focus", "Full Stack, GIS, Game Dev"),
    ("Interests", "Maps, 3D, Animation"),
    ("Hobbies", "Building, Breaking, Rebuilding"),
    (None, "Contact"),
    ("Timezone", "GST (UTC+4)"),
    ("GitHub", "github.com/" + USER),
]
QUOTE = ["// Every bug is a feature", "// that hasn't told its joke yet."]

WIDTH = 60  # right column, in characters
BG, FG, DIM, KEY, VAL = "#161b22", "#c9d1d9", "#616e7f", "#d2a8ff", "#7ee787"
ADD, DEL = "#3fb950", "#f85149"

# ---------------------------------------------------------------- portrait
COLS, ROWS, CW, CH = 48, 26, 10, 20  # cell is 1:2, like a monospace glyph
SKIN, HAIR, EYE, LIP, TEETH, SUIT, SHIRT, HAT, BAND = range(1, 10)
COLOR = {SKIN: "#e6edf3", HAIR: "#3fb950", EYE: "#8957e5", LIP: "#f85149",
         TEETH: "#ffffff", SUIT: "#a371f7", SHIRT: "#2ea043", HAT: "#a371f7", BAND: "#553098"}
RAMP = "░▒▓█"


def draw_face():
    w, h = COLS * CW, ROWS * CH
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    cx, cy = 240, 195
    spikes = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
              for i, a in enumerate(range(150, 391, 10)) for r in [(125, 185)[i % 2]]]
    d.polygon(spikes, fill=HAIR)
    d.ellipse((124, 225, 156, 295), fill=SKIN)  # ears
    d.ellipse((324, 225, 356, 295), fill=SKIN)
    d.polygon([(0, h), (25, 455), (185, 418), (295, 418), (455, 455), (w, h)], fill=SUIT)
    d.polygon([(195, 425), (285, 425), (240, h)], fill=SHIRT)
    d.rectangle((205, 370, 275, 440), fill=SKIN)  # neck
    d.ellipse((138, 112, 342, 405), fill=SKIN)
    for tri in [[(150, 160), (205, 120), (185, 205)], [(195, 125), (260, 118), (225, 195)],
                [(245, 120), (300, 130), (270, 200)], [(290, 125), (335, 165), (305, 210)],
                [(140, 175), (170, 150), (162, 265)], [(310, 150), (342, 175), (320, 265)]]:
        d.polygon(tri, fill=HAIR)  # fringe falling over the forehead
    d.rectangle((0, 0, w, 128), fill=0)  # hair only spills out below the brim
    d.polygon([(155, 128), (168, 22), (312, 22), (325, 128)], fill=HAT)  # fedora crown
    d.rectangle((152, 100, 328, 120), fill=BAND)
    d.ellipse((55, 114, 425, 146), fill=HAT)  # brim; bottom kept above y=150 so no stub leaks into the next row
    d.ellipse((172, 218, 230, 268), fill=EYE)  # smudged eye paint
    d.ellipse((250, 218, 308, 268), fill=EYE)
    d.line([(168, 205), (232, 220)], fill=EYE, width=12)  # brows angled down
    d.line([(248, 220), (312, 205)], fill=EYE, width=12)
    d.ellipse((196, 243, 214, 257), fill=TEETH)  # glint, centred on a cell
    d.ellipse((266, 243, 284, 257), fill=TEETH)
    # Crescent grin on the half-row grid: a half row is 10px here, so one "pixel" is a 10x10 square.
    # Mid-mouth edges at y 320/330/340/360 put the samples (325, 335, 345, 355) on 1px upper lip,
    # 1px dark line and 2px lower lip; every edge meets at the tips, so the crescent tapers to points.
    tips = (150, 295), (330, 295)
    mid = lambda y: 2 * y - 295  # control point whose curve passes through y at mid-mouth
    d.polygon(curve(tips, mid(320)) + curve(tips, mid(360))[::-1], fill=LIP)
    d.polygon(curve(tips, mid(330)) + curve(tips, mid(340))[::-1], fill=0)  # dark line between the lips
    d.line([(150, 295), (140, 278), (138, 258)], fill=LIP, width=10)  # scars curling to the cheeks
    d.line([(330, 295), (340, 278), (342, 258)], fill=LIP, width=10)
    return img


def curve(ends, cy, cx=None, n=24):
    """Points on the quadratic Bezier from ends[0] to ends[1] with control (cx, cy); cx defaults to the middle."""
    (x0, y0), (x2, y2) = ends
    cx = (x0 + x2) / 2 if cx is None else cx
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x2,
             (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y2) for t in (i / n for i in range(n + 1))]


def portrait():
    img = draw_face()
    w, _ = img.size
    blur = {k: img.point(lambda p, k=k: 255 if p == k else 0).filter(ImageFilter.GaussianBlur(9))
            for k in COLOR}
    rng = random.Random(7)
    rows, under = [], []
    for r in range(ROWS):
        row, low = [], []
        for c in range(COLS):
            x, y = c * CW + CW // 2, r * CH + CH // 2
            k = img.getpixel((x, y))
            top, bot = img.getpixel((x, y - CH // 4)), img.getpixel((x, y + CH // 4))
            low.append((" ", None))
            if LIP in (top, bot) and top != bot:  # half-row detail: ▀ in the top colour over a ▄ underlay
                row.append(("▀", COLOR[top]) if top else ("▄", COLOR[bot]))
                if top and bot:
                    low[-1] = ("▄", COLOR[bot])
                continue
            if not k:
                below = img.getpixel((x, y + CH)) if y + CH < img.size[1] else 0
                # half-block edge on top of the hat, skipping the middle for the crown's pinch
                hat_top = below == HAT and abs(x - 240) > 20
                row.append(("▄", COLOR[HAT]) if hat_top else (" ", None))
                continue
            shade = blur[k].getpixel((x, y)) / 255 * (0.8 + 0.2 * (w - x) / w)  # lit from the left
            ch = RAMP[min(3, int(shade * 4))]
            if k in (HAT, BAND, LIP):
                ch = "█"  # solid felt and paint; edge shading turns thin shapes into ░
            elif k == HAIR and shade < 0.85:
                ch = rng.choice("~≈~▒")
            row.append((ch, COLOR[k]))
        rows.append(row)
        under.append(low)
    return under, rows  # paint order: the underlay first


# ---------------------------------------------------------------- stats
def api(url, body=None):
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(url, json.dumps(body).encode() if body else None,
                                 {"Authorization": "bearer " + token})
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read() or "null")
    except urllib.error.HTTPError as e:
        if body or e.code not in (403, 404, 409):  # unreadable or empty repo: skip it, fail on the rest
            raise
        return e.code, None


def gql(query, **variables):
    _, data = api("https://api.github.com/graphql", {"query": query, "variables": variables})
    if data.get("errors"):
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def loc(owner, repo):
    """(added, deleted) lines by USER on the repo's default branch; (0, 0) if unreadable."""
    for _ in range(6):  # GitHub answers 202 while it computes the numbers
        status, data = api("https://api.github.com/repos/%s/%s/stats/contributors" % (owner, repo))
        if status != 202:
            break
        time.sleep(3)
    for person in (data if status == 200 else None) or []:
        if (person.get("author") or {}).get("login") == USER:
            return sum(w["a"] for w in person["weeks"]), sum(w["d"] for w in person["weeks"])
    return 0, 0


def stats():
    """Live numbers for USER's whole account (public contributions with the workflow's token)."""
    # shortcut: first 100 owned repos only, paginate if the account ever passes that
    u = gql("""query($l:String!){user(login:$l){createdAt followers{totalCount}
      repositories(ownerAffiliations:OWNER,isFork:false,first:100){totalCount nodes{name stargazerCount}}}}""",
            l=USER)
    commits = 0
    for year in range(int(u["createdAt"][:4]), dt.date.today().year + 1):
        commits += gql("""query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){
          contributionsCollection(from:$f,to:$t){totalCommitContributions}}}""",
                       l=USER, f="%d-01-01T00:00:00Z" % year, t="%d-12-31T23:59:59Z" % year,
                       )["contributionsCollection"]["totalCommitContributions"]
    mine = [loc(USER, r["name"]) for r in u["repositories"]["nodes"]]
    return {"repos": u["repositories"]["totalCount"],
            "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
            "followers": u["followers"]["totalCount"], "commits": commits,
            "add": sum(a for a, _ in mine), "del": sum(d for _, d in mine)}


# ---------------------------------------------------------------- layout
def field(key, value, width, lead=". "):
    """'. Key: ...... value' padded to width, as [(text, color)]."""
    dots = width - len(lead + key + ": ") - len(value) - 1
    return [(lead, FG), (key, KEY), (": ", FG), ("." * max(dots, 1) + " ", DIM), (value, VAL)]


def header(title):
    text = "- " + title + " " if title else ""
    return [(text, FG), ("—" * (WIDTH - len(text) - 3) + "-—-", DIM)]


def pair(k1, v1, k2, v2, half=30):
    return field(k1, v1, half) + [(" | ", FG)] + field(k2, v2, WIDTH - half - 3, lead="")


def loc_line(s):
    a, r = "{:,}++".format(s["add"]), "{:,}--".format(s["del"])
    net = field("Lines of Code", "{:,} ( ".format(s["add"] - s["del"]), WIDTH - len(a + ", " + r + " )"))
    return net + [(a, ADD), (", ", FG), (r, DEL), (" )", FG)]


def right_column(s):
    head = USER + "@github "
    lines = [[(head, FG), ("—" * (WIDTH - len(head) - 3) + "-—-", DIM)]]
    for key, value in INFO:
        lines.append(header(value) if key is None else field(key, value, WIDTH))
    lines += [header("Personal"),
              pair("Repos", str(s["repos"]), "Stars", str(s["stars"])),
              pair("Commits", "{:,}".format(s["commits"]), "Followers", str(s["followers"])),
              loc_line(s),
              header("")[1:]]
    lines += [[(q.rjust(WIDTH), DIM)] for q in QUOTE]
    return lines


def tspans(segments):
    out, run, color = [], "", None
    for text, c in segments + [("", "end")]:
        if c != color and run:
            out.append('<tspan fill="%s">%s</tspan>' % (color, escape(run)) if color else escape(run))
            run = ""
        run, color = run + text, c
    return "".join(out)


def svg(layers, info):
    lh, top, art_x, info_x = 17, 30, 20, 420
    rows = []
    for layer in layers:  # same x/y and forced width per row, so the layers line up glyph for glyph
        for i, row in enumerate(layer):
            if any(ch != " " for ch, _ in row):
                rows.append('<tspan x="%d" y="%d" textLength="%d" lengthAdjust="spacingAndGlyphs">%s</tspan>'
                            % (art_x, top + i * lh, COLS * 8, tspans(list(row))))
    for i, line in enumerate(info):
        rows.append('<tspan x="%d" y="%d">%s</tspan>' % (info_x, top + i * lh, tspans(line)))
    height = top + ROWS * lh
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="950" height="%d" '
            'font-family="Consolas,\'DejaVu Sans Mono\',\'Courier New\',monospace" font-size="14">'
            '<rect width="100%%" height="100%%" rx="15" fill="%s"/>'
            '<text xml:space="preserve" fill="%s">\n%s\n</text></svg>\n'
            % (height, BG, FG, "\n".join(rows)))


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "card.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg(portrait(), right_column(stats())))
    print("wrote", out)
