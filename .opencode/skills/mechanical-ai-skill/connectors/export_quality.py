"""Export Quality Signals — "what I can and cannot see in this file, and why".

This is the Review Quality Layer, kept deliberately SEPARATE from Format
Intelligence:

  - Format Intelligence answers "you handed me the WRONG KIND of file"
    (SLDASM / IGS / STL) -> needs_input, swap the file.
  - Export Quality Signals answers "you handed me the RIGHT kind of file, but
    it was EXPORTED in a way that costs me information" -> status stays ok, but
    the report must say what was lost so the user is never misled.

Philosophy: the skill's job here is not to be always right — it is to know, and
SAY, when it cannot judge. Every signal reports three honest things:
    seen      — what the file does contain
    not_seen  — what is missing / unavailable
    cannot_judge — which downstream conclusions are therefore unsafe

All signals are computed from the STEP text already in hand — no geometry kernel,
no invention. A signal that cannot be computed is omitted, never guessed.

Each signal returns a dict or None:
    {"signal": <id>, "severity": "info|warn", "seen": {...}, "not_seen": [...],
     "cannot_judge": [...], "message": "<one-line human summary>"}

Community: emits the signals (the WHAT). Coverage percentages and any
remediation guidance beyond "re-export with structure" are Professional.
"""

# --- thresholds (transparent, tunable; no hidden magic) ---
_FLAT_SOLID_MIN = 5      # solids that outnumber products this much => flattened
_FLAT_PARTS_MAX = 1      # "single product" ceiling for geometry_only_export
_FLAT_BOM_DEPTH = 1      # depth-1 with many parts => structure squashed
_FLAT_BOM_PARTS_MIN = 20
_MISSING_NAMES_FRAC = 0.5  # >=50% unresolved/blank names => names unusable


def geometry_only_export(bom):
    """1 PRODUCT but many discrete solid bodies => assembly tree stripped on export.

    The single most dangerous case: structure-level counts say "1 part, low
    complexity", while the geometry holds dozens/hundreds of bodies. Correct
    numbers, misleading conclusion. We surface the discrepancy as a signal.
    """
    parts = bom.get("unique_parts", 0)
    solids = bom.get("solid_bodies", 0)
    if parts <= _FLAT_PARTS_MAX and solids >= _FLAT_SOLID_MIN:
        ti = bom.get("total_instances", 0) or 0
        if ti > 1:
            return {
                "signal": "parser_inconsistency",
                "severity": "warn",
                "seen": {"products": parts, "total_instances": ti,
                         "solid_bodies": solids},
                "not_seen": ["resolved BOM (unique_parts=0 despite "
                             + str(ti) + " assembly instances)"],
                "cannot_judge": ["part count", "BOM", "mechanism", "vendor mix",
                                 "complexity", "risk"],
                "message": ("Parser inconsistency: " + str(ti) + " assembly "
                            "instances present (structure exists) but BOM resolved "
                            "to " + str(parts) + " parts. Conflicting parser signals "
                            "- cannot assess. NOT a geometry-only export."),
            }
        return {
            "signal": "geometry_only_export",
            "severity": "warn",
            "seen": {"products": parts, "solid_bodies": solids},
            "not_seen": ["assembly-usage links (NAUO)", "per-part identity",
                         "sub-assembly hierarchy"],
            "cannot_judge": ["part count", "BOM", "mechanism", "vendor mix",
                             "complexity", "risk"],
            "message": (f"Geometry-only export: {parts} PRODUCT but {solids} solid "
                        f"bodies. Assembly structure was not preserved on export — "
                        f"part/BOM/mechanism analysis cannot run on a flattened solid. "
                        f"Re-export with assembly/product structure enabled."),
        }
    return None


def flat_bom_export(bom):
    """Many parts but depth 1 => hierarchy collapsed (all parts dumped at top).

    Less severe than geometry_only_export (parts ARE individuated), but the
    sub-assembly structure — which drives assembly-sequence and mechanism
    grouping — is gone.
    """
    parts = bom.get("unique_parts", 0)
    depth = bom.get("assembly_depth")
    if depth == _FLAT_BOM_DEPTH and parts >= _FLAT_BOM_PARTS_MIN:
        return {
            "signal": "flat_bom_export",
            "severity": "warn",
            "seen": {"unique_parts": parts, "assembly_depth": depth},
            "not_seen": ["sub-assembly grouping", "assembly hierarchy"],
            "cannot_judge": ["assembly sequence", "mechanism grouping by sub-assembly"],
            "message": (f"Flat BOM: {parts} parts at a single level (depth 1). "
                        f"Sub-assembly structure was not preserved; per-part data "
                        f"is fine but grouping/sequence cannot be inferred."),
        }
    return None


def missing_names(bom):
    """A large fraction of instances have no resolvable name => names unusable.

    When names are missing, vendor/category/mechanism rules (all name-driven)
    are blind regardless of how good the rules are. Say so, rather than
    reporting "0 vendors" as if the assembly genuinely had none.
    """
    total = bom.get("total_instances", 0)
    unresolved = bom.get("unresolved_instances", 0)
    if total and unresolved / total >= _MISSING_NAMES_FRAC:
        frac = round(100 * unresolved / total)
        return {
            "signal": "missing_names",
            "severity": "warn",
            "seen": {"total_instances": total, "unresolved_instances": unresolved},
            "not_seen": [f"{frac}% of part names"],
            "cannot_judge": ["vendor identification", "category classification",
                             "mechanism detection (all name-driven)"],
            "message": (f"{frac}% of instances have no resolvable name. Name-driven "
                        f"analysis (vendor/category/mechanism) is unreliable for this "
                        f"file — a '0 vendors' result reflects missing names, not "
                        f"absence of vendors."),
        }
    return None


def classification_coverage(bom, classified_instances):
    """A large fraction of instances fell into no category => coverage is low.

    The dangerous case the belt conveyor exposed: "100% commercial" computed over
    only the classified subset (36 of 212) reads as a confident statement about
    the whole assembly, when 176 instances were simply never classified. We say
    the coverage explicitly so "100%" is never mistaken for "100% of everything".

    classified_instances: how many instances landed in ANY category (custom or
    commercial). Compared against total_instances.
    """
    total = bom.get("total_instances", 0)
    if not total or classified_instances is None:
        return None
    unknown = max(0, total - classified_instances)
    cov = round(100 * classified_instances / total)
    if cov < 60:  # below 60% classified => statistics speak for a minority
        return {
            "signal": "unknown_part_ratio",
            "severity": "warn" if cov < 40 else "info",
            "seen": {"classified_instances": classified_instances, "total_instances": total,
                     "coverage_pct": cov},
            "not_seen": [f"{unknown} of {total} instances ({100 - cov}%) unclassified"],
            "cannot_judge": ["manufacturing mix for the full assembly",
                             "category statistics for the full assembly"],
            "message": (f"Classification coverage {cov}%: {classified_instances} of {total} "
                        f"instances classified, {unknown} not. Manufacturing-mix and category "
                        f"statistics describe only the classified subset, not the whole assembly."),
        }
    return None


def unicode_encoded_names(bom, decoded_any):
    """STEP carried ISO-10303-21 \\X2\\ Unicode names (e.g. Chinese exports).

    Informational, not a problem — we decode them. We note it so the user knows
    the names they see were reconstructed, not raw ASCII.
    """
    if decoded_any:
        return {
            "signal": "unicode_encoded_names",
            "severity": "info",
            "seen": {"unicode_encoded": True},
            "not_seen": [],
            "cannot_judge": [],
            "message": ("Part names were Unicode-encoded in the STEP (\\X2\\ ISO-10303-21) "
                        "and have been decoded. Names shown are reconstructed."),
        }
    return None


# Registry — extensible. v0.7.4 ships geometry_only_export (validated on a real
# 120MB NX flattened export, 1 PRODUCT / 723 solids). The rest are wired but
# conservative; v0.7.5 (Review Quality Signals) adds coverage-percentage signals
# (vendor_coverage_low, category_coverage_low, unknown_part_pct).
def assess(bom, decoded_any=False, classified_instances=None):
    """Run all export-quality signals; return the list that fired (order = severity)."""
    signals = []
    for fn, args in (
        (geometry_only_export, (bom,)),
        (flat_bom_export, (bom,)),
        (missing_names, (bom,)),
        (classification_coverage, (bom, classified_instances)),
        (unicode_encoded_names, (bom, decoded_any)),
    ):
        try:
            s = fn(*args)
        except Exception:
            s = None
        if s:
            signals.append(s)
    # If a structural signal already blocks the whole review, coverage/missing-name
    # signals are redundant noise (everything is unjudgeable already) — drop them.
    ids = {s["signal"] for s in signals}
    if ids & _BLOCKING:
        signals = [s for s in signals
                   if s["signal"] in _BLOCKING or s["signal"] == "unicode_encoded_names"]
    # warns before infos
    signals.sort(key=lambda s: 0 if s["severity"] == "warn" else 1)
    return signals


# --- Assessment Status: one honest verdict on whether this file can be reviewed ---
# PASS    — structure present, names usable; downstream conclusions are sound.
# PARTIAL — analysable, but a quality signal limits some conclusions (e.g. low
#           classification coverage, many missing names) — numbers stand but are
#           scoped, not whole-assembly.
# BLOCKED — a structural signal removes the basis for review entirely
#           (geometry_only_export / flat dump) — part/BOM/mechanism/risk are
#           Not Assessable, and the report must say so instead of printing Low/100.
_BLOCKING = {"geometry_only_export", "parser_inconsistency"}
_PARTIAL = {"flat_bom_export", "missing_names", "unknown_part_ratio"}

# Per-check status for the Analysis Quality table.
_CHECKS = ["Assembly Structure", "Part Identity", "BOM Generation",
           "Mechanism Detection", "Vendor Detection"]


def confidence_score(dims):
    """Review Confidence as a transparent four-dimension weighted score (0-100).

    NOT a quality judgement of the design — it scores HOW MUCH OF THE FILE THE
    SKILL COULD SEE, dimension by dimension, so an engineer reads "Medium (65)"
    together with the breakdown and knows *which* part is weak (e.g. category
    coverage low) rather than guessing.

    The product is a STEP-text understanding engine, so Structure carries the
    most weight: if the assembly structure is gone, nothing else can be trusted.

      Structure   40%   (NAUO present, not flattened, depth sane)
      Category    25%   (fraction of instances classified)
      Mechanism   20%   (any mechanism detected, confidence-weighted)
      Vendor      15%   (fraction of unique parts vendor-matched)

    dims: dict of {structure, category, mechanism, vendor} each 0..100.
    Returns (score, band, breakdown[]) — breakdown is per-dimension contribution.
    """
    weights = [("Structure", "structure", 40),
               ("Category", "category", 25),
               ("Mechanism", "mechanism", 20),
               ("Vendor", "vendor", 15)]
    breakdown = []
    score = 0.0
    for label, key, w in weights:
        pct = max(0, min(100, dims.get(key, 0)))
        contrib = pct / 100 * w
        score += contrib
        breakdown.append({"dimension": label, "coverage_pct": round(pct),
                          "weight": w, "contribution": round(contrib)})
    score = round(score)
    band = ("High" if score >= 80 else "Medium" if score >= 50
            else "Low" if score >= 25 else "Very Low")
    return score, band, breakdown


def assessment_status(signals):
    """Derive overall PASS/PARTIAL/BLOCKED + per-check PASS/FAIL/PARTIAL from signals.

    Returns {status, reason, checks: {name: PASS|FAIL|PARTIAL}, not_assessable: [...]}.
    not_assessable lists the downstream conclusions that must be shown as
    'Not Assessable' rather than printed with a misleading value.
    """
    ids = {s["signal"] for s in signals}
    checks = {c: "PASS" for c in _CHECKS}
    not_assessable = []
    if ids & _BLOCKING:
        status = "BLOCKED"
        if "parser_inconsistency" in ids:
            reason = ("conflicting parser signals: structure present "
                      "(total_instances>1) but BOM empty - cannot assess")
        else:
            reason = "Assembly structure not preserved on export"
        for c in _CHECKS:
            checks[c] = "FAIL"
        not_assessable = ["complexity", "risk", "manufacturing_mix",
                          "part count", "BOM", "mechanism", "vendor mix"]
    elif ids & _PARTIAL:
        status = "PARTIAL"
        if "unknown_part_ratio" in ids:
            reason = "Low classification coverage; some statistics scoped to a subset"
        elif "missing_names" in ids:
            reason = "Many part names unresolved; name-driven detection limited"
            checks["Part Identity"] = "PARTIAL"
            checks["Vendor Detection"] = "PARTIAL"
            checks["Mechanism Detection"] = "PARTIAL"
        else:
            reason = "Sub-assembly hierarchy not preserved"
            checks["Assembly Structure"] = "PARTIAL"
    else:
        status = "PASS"
        reason = "Structure and names usable; conclusions sound"
    return {"status": status, "reason": reason, "checks": checks,
            "not_assessable": not_assessable}
