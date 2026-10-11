import json, re, time
import requests
from bs4 import BeautifulSoup

BASE = "https://pakistani.org"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

def get(path):
    r = requests.get(BASE + path, headers=H, timeout=30)
    r.raise_for_status()
    return r.text

ART_RE = re.compile(r"^(\d{1,3}[A-Z]?)\.?$")

def parse_part(path):
    soup = BeautifulSoup(get(path), "html.parser")
    articles = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) != 2:
            continue
        nobr = tds[0].find("nobr")
        if not nobr:
            continue
        b = nobr.find("b")
        m = ART_RE.match((b or nobr).get_text(strip=True))
        if not m:
            continue
        no = m.group(1)
        # second td: <b>Title</b><br> body...
        for sup in tds[1].find_all("sup"):  # drop footnote markers
            sup.decompose()
        title_tag = tds[1].find("b")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if title_tag:
            title_tag.decompose()
        body = tds[1].get_text("\n", strip=True)
        if body:
            articles.append({"article": no, "title": title, "text": body, "source": BASE + path})
    return articles

def clean_lines(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    text = soup.get_text("\n")
    return [l.strip() for l in text.split("\n") if l.strip()]


def parse_schedule(path, name, subtitle):
    lines = clean_lines(get(path))
    start = 0
    for j, l in enumerate(lines):
        if l == name:
            start = j
            break
    body = []
    for l in lines[start:]:
        if l in ("Go to:", "The Constitution of Pakistan"):
            break
        body.append(l)
    text = "\n".join(body)
    text = text.replace(name, "", 1).replace(subtitle, "", 1).strip()
    return {"article": name, "title": subtitle, "text": text, "source": BASE + path}


def main():
    idx = get("/pakistan/constitution/")
    soup = BeautifulSoup(idx, "html.parser")
    part_paths = sorted({a["href"] for a in soup.find_all("a", href=True)
                         if re.match(r"^/pakistan/constitution/part\d+(\.ch\d+[A-Z]?)?\.html$", a["href"] or "")})
    sched_paths = sorted({a["href"] for a in soup.find_all("a", href=True)
                          if re.match(r"^/pakistan/constitution/schedules/schedule[1-5]\.html$", a["href"] or "")})
    print("part pages:", len(part_paths), "| schedules:", len(sched_paths))
    all_articles, seen = [], set()
    for p in part_paths:
        arts = parse_part(p)
        print(p, "->", len(arts))
        for a in arts:
            if a["article"] in seen:
                continue
            seen.add(a["article"])
            all_articles.append(a)
        time.sleep(0.4)
    sched_info = [
        ("First Schedule", "Laws exempted from the operation of Article 8(1) and (2)"),
        ("Second Schedule", "Election of President"),
        ("Third Schedule", "Oaths of Office"),
        ("Fourth Schedule", "Legislative Lists"),
        ("Fifth Schedule", "Remuneration and Terms and Conditions of Service of Judges"),
    ]
    for (name, subtitle), p in zip(sched_info, sched_paths):
        s = parse_schedule(p, name, subtitle)
        print(p, "->", len(s["text"]), "chars")
        all_articles.append(s)
        time.sleep(0.4)

    def key(a):
        m = re.match(r"(\d+)([A-Z]?)", a["article"])
        if m:
            return (0, int(m.group(1)), m.group(2))
        return (1, 0, a["article"])
    all_articles.sort(key=key)
    json.dump(all_articles, open("articles.json", "w"), indent=1, ensure_ascii=False)
    print("TOTAL:", len(all_articles), "| first:", all_articles[0]["article"], "| last:", all_articles[-1]["article"])
    have = {a["article"] for a in all_articles}
    missing = [str(i) for i in range(1, 281) if str(i) not in have]
    print("missing plain 1-280:", missing)
    empties = [a["article"] for a in all_articles if not a["text"] or len(a["text"]) < 20]
    print("suspiciously short:", empties)

if __name__ == "__main__":
    main()
