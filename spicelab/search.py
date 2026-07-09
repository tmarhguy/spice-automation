"""Generic binary search for closure problems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SearchHistoryEntry:
    value: float
    ok: bool
    meta: dict


@dataclass
class BinarySearchResult:
    best_value: float
    best_meta: dict
    fail_meta: dict
    history: list[SearchHistoryEntry] = field(default_factory=list)


def binary_search(
    evaluate: Callable[[float], tuple[bool, dict]],
    lo: float,
    hi: float,
    tol: float,
) -> BinarySearchResult:
    """
  Search for minimum value in [lo, hi] where evaluate returns (ok, meta).
  Assumes ok(hi) is True and ok(lo) is False (or returns lo if ok(lo)).
    """
    ok_hi, meta_hi = evaluate(hi)
    ok_lo, meta_lo = evaluate(lo)

    if not ok_hi:
        raise RuntimeError(
            f"Even upper bound {hi} fails (meta={meta_hi}). Cannot bracket solution."
        )
    if ok_lo:
        return BinarySearchResult(
            best_value=lo,
            best_meta=meta_lo,
            fail_meta=meta_hi,
            history=[],
        )

    history: list[SearchHistoryEntry] = []
    while (hi - lo) > tol:
        mid = 0.5 * (lo + hi)
        ok, meta = evaluate(mid)
        history.append(SearchHistoryEntry(value=mid, ok=ok, meta=meta))
        if ok:
            hi = mid
            meta_hi = meta
        else:
            lo = mid
            meta_lo = meta

    return BinarySearchResult(
        best_value=hi,
        best_meta=meta_hi,
        fail_meta=meta_lo,
        history=history,
    )
