"""Canned agent replies for the 5 Project Atlas meetings (used with FakeLlmClient)."""

from typing import Any


def extractor_replies() -> list[dict[str, Any]]:
    kickoff = {
        "decisions": [
            {
                "subject": "Database choice",
                "summary": "PostgreSQL is the main database.",
                "decided_by": "Maya Chen",
                "lines": [11, 15],
            }
        ],
        "action_items": [
            {
                "subject": "ingestion api",
                "task": "Own the ingestion API and write its contract.",
                "owner": "Hussnain Razaq",
                "due": "Wednesday",
                "lines": [18, 19],
            }
        ],
        "open_items": [
            {"subject": "data retention", "question": "90 days or one year?", "lines": [22, 99]}
        ],
    }
    review = {
        "decisions": [
            {
                "subject": "architecture approach",
                "summary": "Go event-driven (option B).",
                "decided_by": "Maya Chen",
                "lines": [10],
            }
        ],
        "action_items": [
            {
                "subject": "on-call runbook",
                "task": "Write the on-call runbook.",
                "owner": None,
                "lines": [11, 12],
            }
        ],
        "open_items": [],
    }
    data_model = {
        "decisions": [
            {
                "subject": "database choice",
                "summary": "Switch to MongoDB.",
                "decided_by": "Maya Chen",
                "reason": "Event schema changes too often.",
                "lines": [7],
            },
            {"subject": "made up", "summary": "Not grounded.", "lines": [500]},
        ],
        "action_items": [
            {
                "subject": "ingestion api",
                "task": "Build the ingestion prototype on MongoDB.",
                "owner": "Hussnain Razaq",
                "due": "Friday, October 9",
                "lines": [9],
            }
        ],
        "open_items": [],
    }
    empty: dict[str, Any] = {"decisions": [], "action_items": [], "open_items": []}
    retention_again = {
        "decisions": [],
        "action_items": [],
        "open_items": [{"subject": "data retention", "question": "Still open.", "lines": [7]}],
    }
    return [kickoff, review, data_model, empty, retention_again]


def stance_reply() -> dict[str, Any]:
    return {
        "stances": [
            {
                "person": "Priya Nair",
                "subject": "architecture approach",
                "leaning": "still prefers batch",
                "trend": "softened",
                "explanation": "She seems to accept it but keeps a fallback.",
                "evidence": [{"meeting_id": 3, "line": 14}, {"meeting_id": 5, "line": 4}],
            },
            {
                "person": "Omar Haddad",
                "subject": "x",
                "leaning": "y",
                "trend": "unchanged",
                "explanation": "Only one line.",
                "evidence": [{"meeting_id": 1, "line": 3}],
            },
        ]
    }


def timeline_reply() -> dict[str, Any]:
    return {
        "changes": [
            {
                "meeting_id": 3,
                "subject": "database choice",
                "change": "Database switched from PostgreSQL to MongoDB.",
                "reason": "Event schema changes too often.",
                "evidence": [{"meeting_id": 3, "line": 7}],
            }
        ]
    }
