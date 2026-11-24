"""Registry for the three check groups. No CLI or report layer here."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckInfo:
    id: str
    group: str
    title: str
    docs_path: str


CHECKS: tuple[CheckInfo, ...] = (
    CheckInfo(
        "CT-START-001",
        "startup",
        "Server starts and completes handshake",
        "docs/checks/CT-START-001.md",
    ),
    CheckInfo(
        "CT-START-002",
        "startup",
        "Handshake reports server name and version",
        "docs/checks/CT-START-002.md",
    ),
    CheckInfo(
        "CT-START-003", "startup", "tools/list works", "docs/checks/CT-START-003.md"
    ),
    CheckInfo(
        "CT-START-004",
        "startup",
        "No non-protocol text on stdout",
        "docs/checks/CT-START-004.md",
    ),
    CheckInfo(
        "CT-START-005",
        "startup",
        "Server exits after input is closed",
        "docs/checks/CT-START-005.md",
    ),
    CheckInfo(
        "CT-DESC-001",
        "description/schema basics",
        "Every tool has a description",
        "docs/checks/CT-DESC-001.md",
    ),
    CheckInfo(
        "CT-DESC-002",
        "description/schema basics",
        "Description length is within limits",
        "docs/checks/CT-DESC-002.md",
    ),
    CheckInfo(
        "CT-DESC-003",
        "description/schema basics",
        "Tool names are unique",
        "docs/checks/CT-DESC-003.md",
    ),
    CheckInfo(
        "CT-DESC-004",
        "description/schema basics",
        "Every tool has an object inputSchema",
        "docs/checks/CT-DESC-004.md",
    ),
    CheckInfo(
        "CT-DESC-005",
        "description/schema basics",
        "Every top-level property is typed",
        "docs/checks/CT-DESC-005.md",
    ),
    CheckInfo(
        "CT-DESC-006",
        "description/schema basics",
        "Every top-level property has a description",
        "docs/checks/CT-DESC-006.md",
    ),
    CheckInfo(
        "CT-DESC-007",
        "description/schema basics",
        "No hidden characters in scanned text",
        "docs/checks/CT-DESC-007.md",
    ),
    CheckInfo(
        "CT-DESC-008",
        "description/schema basics",
        "No long horizontal whitespace runs",
        "docs/checks/CT-DESC-008.md",
    ),
    CheckInfo(
        "CT-DESC-009",
        "description/schema basics",
        "Tool names match the spec name rule",
        "docs/checks/CT-DESC-009.md",
    ),
    CheckInfo(
        "CT-ROB-001",
        "robustness",
        "Wrong-type input is rejected",
        "docs/checks/CT-ROB-001.md",
    ),
    CheckInfo(
        "CT-ROB-002",
        "robustness",
        "Missing required input is rejected",
        "docs/checks/CT-ROB-002.md",
    ),
    CheckInfo(
        "CT-ROB-003",
        "robustness",
        "Unknown tool name is rejected",
        "docs/checks/CT-ROB-003.md",
    ),
    CheckInfo(
        "CT-ROB-004",
        "robustness",
        "Large string input is handled",
        "docs/checks/CT-ROB-004.md",
    ),
    CheckInfo(
        "CT-ROB-005",
        "robustness",
        "Valid read-only call succeeds",
        "docs/checks/CT-ROB-005.md",
    ),
    CheckInfo(
        "CT-ROB-006",
        "robustness",
        "Server remains responsive after probes",
        "docs/checks/CT-ROB-006.md",
    ),
)

CHECK_IDS: tuple[str, ...] = tuple(item.id for item in CHECKS)
CHECK_BY_ID: dict[str, CheckInfo] = {item.id: item for item in CHECKS}

__all__ = ["CHECKS", "CHECK_BY_ID", "CHECK_IDS", "CheckInfo"]
