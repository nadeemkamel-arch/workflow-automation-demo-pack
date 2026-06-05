from __future__ import annotations

from pathlib import Path

from conversation_flow_qa import analyze, check_row


def test_opt_out_suppresses_future_campaign_messages() -> None:
    result = check_row(
        {
            "id": "MSG-X",
            "campaign": "winback",
            "message": "STOP texting me",
            "customer_status": "lapsed",
            "last_appointment_days": "200",
        }
    )

    assert result.intent == "opt_out"
    assert result.route == "suppress_and_confirm"
    assert "suppress_future_campaigns" in result.quality_checks


def test_reaction_or_complaint_requires_human_review() -> None:
    result = check_row(
        {
            "id": "MSG-Y",
            "campaign": "post_visit",
            "message": "My skin reacted badly after the service.",
            "customer_status": "active",
            "last_appointment_days": "2",
        }
    )

    assert result.intent == "service_recovery"
    assert result.route == "human_owner_review"
    assert "avoid_medical_advice" in result.quality_checks


def test_schedule_request_keeps_ai_behind_review() -> None:
    result = check_row(
        {
            "id": "MSG-Z",
            "campaign": "rebooking",
            "message": "Can you book me next Friday afternoon?",
            "customer_status": "active",
            "last_appointment_days": "45",
        }
    )

    assert result.intent == "schedule_request"
    assert result.route == "ai_draft_then_human_review"
    assert "two preferred windows" in result.draft_response_rule


def test_demo_messages_cover_critical_routes() -> None:
    demo_dir = Path(__file__).parent
    results = analyze(demo_dir / "input" / "customer_messages.csv")
    routes = {item.route for item in results}

    assert len(results) == 12
    assert "suppress_and_confirm" in routes
    assert "human_owner_review" in routes
    assert "manager_policy_review" in routes
    assert "ai_draft_then_human_review" in routes
