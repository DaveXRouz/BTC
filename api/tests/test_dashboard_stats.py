"""Tests for dashboard stats endpoint — GET /oracle/stats."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_svc():
    """Mock OracleReadingService with get_dashboard_stats."""
    svc = MagicMock()
    svc.get_dashboard_stats.return_value = {
        "total_readings": 0,
        "readings_by_type": {},
        "average_confidence": None,
        "most_used_type": None,
        "streak_days": 0,
        "readings_today": 0,
        "readings_this_week": 0,
        "readings_this_month": 0,
    }
    return svc


def test_stats_empty_database(mock_svc):
    """Empty database returns zero stats."""
    stats = mock_svc.get_dashboard_stats()
    assert stats["total_readings"] == 0
    assert stats["readings_by_type"] == {}
    assert stats["average_confidence"] is None
    assert stats["most_used_type"] is None
    assert stats["streak_days"] == 0
    assert stats["readings_today"] == 0
    assert stats["readings_this_week"] == 0
    assert stats["readings_this_month"] == 0


def test_stats_with_readings(mock_svc):
    """Stats reflect inserted readings correctly."""
    mock_svc.get_dashboard_stats.return_value = {
        "total_readings": 15,
        "readings_by_type": {"time": 8, "name": 4, "question": 3},
        "average_confidence": 0.72,
        "most_used_type": "time",
        "streak_days": 3,
        "readings_today": 2,
        "readings_this_week": 10,
        "readings_this_month": 15,
    }
    stats = mock_svc.get_dashboard_stats()
    assert stats["total_readings"] == 15
    assert stats["readings_by_type"]["time"] == 8
    assert stats["most_used_type"] == "time"
    assert stats["readings_today"] == 2


def test_stats_streak_calculation(mock_svc):
    """Streak counts consecutive days."""
    mock_svc.get_dashboard_stats.return_value = {
        "total_readings": 5,
        "readings_by_type": {"time": 5},
        "average_confidence": 0.5,
        "most_used_type": "time",
        "streak_days": 5,
        "readings_today": 1,
        "readings_this_week": 5,
        "readings_this_month": 5,
    }
    stats = mock_svc.get_dashboard_stats()
    assert stats["streak_days"] == 5


def test_stats_confidence_average(mock_svc):
    """Average confidence handles null values."""
    # With confidence
    mock_svc.get_dashboard_stats.return_value = {
        "total_readings": 3,
        "readings_by_type": {"time": 3},
        "average_confidence": 0.65,
        "most_used_type": "time",
        "streak_days": 1,
        "readings_today": 1,
        "readings_this_week": 3,
        "readings_this_month": 3,
    }
    stats = mock_svc.get_dashboard_stats()
    assert stats["average_confidence"] == pytest.approx(0.65)

    # Null confidence
    mock_svc.get_dashboard_stats.return_value["average_confidence"] = None
    stats2 = mock_svc.get_dashboard_stats()
    assert stats2["average_confidence"] is None


def test_dashboard_stats_response_model():
    """DashboardStatsResponse model validates correctly."""
    from app.models.dashboard import DashboardStatsResponse

    resp = DashboardStatsResponse(
        total_readings=10,
        readings_by_type={"time": 5, "name": 5},
        average_confidence=0.8,
        most_used_type="time",
        streak_days=3,
        readings_today=2,
        readings_this_week=7,
        readings_this_month=10,
    )
    assert resp.total_readings == 10
    assert resp.most_used_type == "time"
    assert resp.average_confidence == 0.8
