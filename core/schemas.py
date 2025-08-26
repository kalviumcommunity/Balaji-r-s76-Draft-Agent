"""
JSON schemas for LinkedIn AI agent structured outputs.
Defines validation schemas for posts, schedules, and metrics artifacts.
"""

POST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"}
        },
        "assets": {
            "type": "array",
            "items": {"type": "string"}
        },
        "cta": {"type": "string"},
        "target_window": {
            "type": "object",
            "properties": {
                "day": {"type": "string", "enum": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                "hour": {"type": "integer", "minimum": 0, "maximum": 23}
            },
            "required": ["day", "hour"]
        },
        "source_snippets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["post_id", "reason"]
            }
        }
    },
    "required": ["id", "title", "body", "tags", "cta", "target_window"]
}

SCHEDULE_SCHEMA = {
    "type": "object",
    "properties": {
        "week_of": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "slots": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"},
                    "day": {"type": "string", "enum": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                    "hour": {"type": "integer", "minimum": 0, "maximum": 23},
                    "status": {"type": "string", "enum": ["planned", "scheduled", "published"], "default": "planned"}
                },
                "required": ["post_id", "day", "hour"]
            }
        }
    },
    "required": ["week_of", "slots"]
}

METRICS_SCHEMA = {
    "type": "object",
    "properties": {
        "post_id": {"type": "string"},
        "impressions": {"type": "integer", "minimum": 0},
        "reactions": {"type": "integer", "minimum": 0},
        "comments": {"type": "integer", "minimum": 0},
        "shares": {"type": "integer", "minimum": 0},
        "clicks": {"type": "integer", "minimum": 0},
        "published_at": {"type": "string", "format": "date-time"},
        "engagement_rate": {"type": "number", "minimum": 0}
    },
    "required": ["post_id", "impressions", "reactions", "comments", "shares", "published_at"]
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "week_of": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "now": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "target_window": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "string"},
                            "hour": {"type": "integer"}
                        }
                    }
                }
            }
        },
        "next": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "target_window": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "string"},
                            "hour": {"type": "integer"}
                        }
                    }
                }
            }
        },
        "later": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "experiment": {"type": "string"}
                }
            }
        }
    },
    "required": ["week_of", "now", "next", "later"]
}