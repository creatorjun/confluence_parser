# domain/model.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PageNode:
    depth: int
    title: str
    html_body: str
