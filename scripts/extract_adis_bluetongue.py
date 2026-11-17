"""Extract bluetongue outbreak counts per country and serotype from EU ADIS
annual "outbreaks overview" reports (PDF).

Each report opens with a summary table: one row per disease (or disease type),
one column per country (ISO3 code). A cell holds the number of outbreaks above a
date (last outbreak); "/" means no outbreak. Numbers are matched to countries by
horizontal position, and to rows by their position just above the row's "/" line.

Usage: python extract_adis_bluetongue.py <pdf_dir> <out_dir>
"""
import re
import sys
import csv
from pathlib import Path
from statistics import median

import pdfplumber

TITLE = "Total of outbreaks by disease"
ISO3 = re.compile(r"^[A-Z]{2,3}$")
INT = re.compile(r"^\d+$")
DATE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def group_lines(words, tol=2.5):
    """Group words into lines by their 'top' coordinate."""
    lines = []
    for w in sorted(words, key=lambda w: w["top"]):
        if lines and abs(lines[-1]["top"] - w["top"]) <= tol:
            lines[-1]["words"].append(w)
        else:
            lines.append({"top": w["top"], "words": [w]})
    return lines


def parse_page(page):
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    text = " ".join(w["text"] for w in words)
    if TITLE not in text:
        return None, []

    # Header: the line holding "Disease / Disease type" and the ISO3 codes
    hdr = next(w for w in words if w["text"] == "Disease")
    header = [w for w in words if abs(w["top"] - hdr["top"]) < 4 and ISO3.match(w["text"])]
    cols = [((w["x0"] + w["x1"]) / 2, w["text"]) for w in header]
    label_limit = min(w["x0"] for w in header) - 10
    body = [w for w in words if w["top"] > hdr["top"] + 8]

    # Row anchors: lines of "/" in the country columns
    slashes = [w for w in body if w["text"] == "/" and w["x0"] > label_limit]
    rows = [ln["top"] for ln in group_lines(slashes) if len(ln["words"]) >= 2]

    lines = group_lines(body)
    records, unassigned = [], []

    def label_for(row_y):
        parts = [w for w in body if w["x1"] < label_limit and row_y - 13 < w["top"] < row_y + 10]
        return " ".join(w["text"] for w in sorted(parts, key=lambda w: (round(w["top"]), w["x0"])))

    for w in body:
        if not (INT.match(w["text"]) and w["x0"] > label_limit):
            continue
        # A count sits just above its row's "/" line (6-12 pt above)
        cands = [r for r in rows if 3 < r - w["top"] < 13]
        xc = (w["x0"] + w["x1"]) / 2
        col = min(cols, key=lambda c: abs(c[0] - xc))
        if not cands or abs(col[0] - xc) > 22:
            unassigned.append((page.page_number, round(w["top"]), w["text"], col[1]))
            continue
        row_y = min(cands, key=lambda r: r - w["top"])
        records.append({"page": page.page_number, "row_y": round(row_y),
                        "label": label_for(row_y), "iso3": col[1], "outbreaks": int(w["text"])})
    return cols, records, unassigned


def serotype_of(label):
    m = re.search(r"/\s*(.+)$", label)
    s = m.group(1).strip() if m else "unspecified"
    return re.sub(r"\s+", " ", s)


def main(pdf_dir, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    detail, problems = [], []
    for pdf in sorted(Path(pdf_dir).glob("*.pdf")):
        year = int(re.search(r"report-(\d{4})", pdf.name).group(1))
        with pdfplumber.open(pdf) as doc:
            for page in doc.pages[:12]:          # the summary table is at the start
                res = parse_page(page)
                if res[0] is None:
                    continue
                cols, recs, unassigned = res
                problems += [(year,) + u for u in unassigned]
                for r in recs:
                    if "luetongue" in r["label"]:
                        detail.append({"year": year, "iso3": r["iso3"],
                                       "serotype": serotype_of(r["label"]),
                                       "outbreaks": r["outbreaks"], "label": r["label"],
                                       "page": r["page"]})
    with open(out_dir / "bluetongue_adis_by_serotype.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["year", "iso3", "serotype", "outbreaks", "label", "page"])
        wr.writeheader()
        wr.writerows(detail)
    totals = {}
    for d in detail:
        totals[(d["iso3"], d["year"])] = totals.get((d["iso3"], d["year"]), 0) + d["outbreaks"]
    with open(out_dir / "bluetongue_adis.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["iso3", "year", "outbreaks", "source"])
        for (iso3, year), n in sorted(totals.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            wr.writerow([iso3, year, n, f"ADIS outbreaks overview report {year}"])
    print(f"{len(detail)} bluetongue cells, {len(totals)} country-years")
    print(f"{len(problems)} integers not assigned to a row/column (all diseases):")
    for p in problems[:40]:
        print("  ", p)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])


# ---------------------------------------------------------------------------
# Harmonise country codes: reports up to 2021 use ISO3 codes, from 2022 ISO2.
ISO2_TO_ISO3 = {
    "AD": "AND", "AL": "ALB", "AT": "AUT", "BA": "BIH", "BE": "BEL", "BG": "BGR", "CH": "CHE",
    "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "ES": "ESP", "FI": "FIN",
    "FR": "FRA", "GR": "GRC", "HR": "HRV", "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA",
    "LT": "LTU", "LU": "LUX", "LV": "LVA", "MD": "MDA", "ME": "MNE", "MK": "MKD", "MT": "MLT",
    "NL": "NLD", "NO": "NOR", "PL": "POL", "PT": "PRT", "RO": "ROU", "RS": "SRB", "SE": "SWE",
    "SI": "SVN", "SK": "SVK", "TR": "TUR", "UA": "UKR", "XK": "XKX", "XKO": "XKX",
    "XI": "GBR",  # Northern Ireland, reported separately after Brexit
}
NAMES = {
    "AND": "Andorra", "ALB": "Albania", "AUT": "Austria", "BIH": "Bosnia and Herzegovina",
    "BEL": "Belgium", "BGR": "Bulgaria", "CHE": "Switzerland", "CYP": "Cyprus",
    "CZE": "Czechia", "DEU": "Germany", "DNK": "Denmark", "EST": "Estonia", "ESP": "Spain",
    "FIN": "Finland", "FRA": "France", "GRC": "Greece", "HRV": "Croatia", "HUN": "Hungary",
    "IRL": "Ireland", "ISL": "Iceland", "ITA": "Italy", "LTU": "Lithuania", "LUX": "Luxembourg",
    "LVA": "Latvia", "MDA": "Moldova", "MNE": "Montenegro", "MKD": "North Macedonia",
    "MLT": "Malta", "NLD": "Netherlands", "NOR": "Norway", "POL": "Poland", "PRT": "Portugal",
    "ROU": "Romania", "SRB": "Serbia", "SWE": "Sweden", "SVN": "Slovenia", "SVK": "Slovakia",
    "TUR": "Turkey", "UKR": "Ukraine", "XKX": "Kosovo", "GBR": "United Kingdom",
}


def harmonise(out_dir):
    out_dir = Path(out_dir)
    rows = list(csv.DictReader(open(out_dir / "bluetongue_adis_by_serotype.csv")))
    for r in rows:
        r["code_in_report"] = r["iso3"]
        r["iso3"] = ISO2_TO_ISO3.get(r["iso3"], r["iso3"])
        r["country"] = NAMES.get(r["iso3"], r["iso3"])
    fields = ["year", "country", "iso3", "code_in_report", "serotype", "outbreaks", "label", "page"]
    with open(out_dir / "bluetongue_adis_by_serotype.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)
    totals = {}
    for r in rows:
        k = (int(r["year"]), r["iso3"])
        totals[k] = totals.get(k, 0) + int(r["outbreaks"])
    with open(out_dir / "bluetongue_adis.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["country", "iso3", "year", "outbreaks", "source"])
        for (year, iso3), n in sorted(totals.items()):
            wr.writerow([NAMES.get(iso3, iso3), iso3, year, n,
                         f"ADIS outbreaks overview report {year}"])
    unknown = sorted({r["iso3"] for r in rows if r["iso3"] not in NAMES})
    print("Unmapped codes:", unknown or "none")


if __name__ == "__main__" and len(sys.argv) > 2:
    harmonise(sys.argv[2])
