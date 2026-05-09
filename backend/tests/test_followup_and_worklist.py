"""Tests for P1.4b follow-up proposal and P1.5 worklist generation."""

from __future__ import annotations

import pytest

from resonantia.services.tool_executor import (
    _propose_follow_up,
    _generate_worklist_tool,
    TOOL_HANDLERS,
)


class TestFollowUpProposal:
    def test_handler_registered(self):
        assert "propose_follow_up_experiment" in TOOL_HANDLERS
        assert TOOL_HANDLERS["propose_follow_up_experiment"] is _propose_follow_up

    @pytest.mark.asyncio
    async def test_missing_experiment_id_returns_error(self):
        result = await _propose_follow_up({}, org_id="org_A")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_nonexistent_experiment_returns_error(self):
        from unittest.mock import AsyncMock, patch

        with patch("resonantia.services.tool_executor.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_session

            result = await _propose_follow_up(
                {"experiment_id": "550e8400-e29b-41d4-a716-446655440000"},
                org_id="org_A",
            )
        assert "error" in result

    def test_follow_up_logic_hit_confirmation(self):
        """Verify hit confirmation option is generated for good IC50."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_exp = MagicMock()
        mock_exp.org_id = "org_A"
        mock_exp.name = "Staurosporine screen"
        mock_exp.results = {
            "ic50": 42.3,
            "hill_slope": -1.18,
            "r_squared": 0.994,
            "z_prime": 0.71,
        }

        with patch("resonantia.services.tool_executor.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_exp)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_session

            result = asyncio.get_event_loop().run_until_complete(
                _propose_follow_up(
                    {"experiment_id": "550e8400-e29b-41d4-a716-446655440000"},
                    org_id="org_A",
                )
            )

        assert "options" in result
        assert len(result["options"]) >= 2
        assert result["options"][0]["title"] == "Hit Confirmation"
        assert result["recommended"] == 1
        range_info = result["options"][0]["concentration_range"]
        assert range_info["start_nM"] < 42.3
        assert range_info["end_nM"] > 42.3

    def test_follow_up_logic_poor_r_squared(self):
        """Poor R² should include re-test option."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_exp = MagicMock()
        mock_exp.org_id = "org_A"
        mock_exp.name = "Weak fit"
        mock_exp.results = {"ic50": 100, "r_squared": 0.75, "z_prime": 0.8}

        with patch("resonantia.services.tool_executor.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_exp)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_session

            result = asyncio.get_event_loop().run_until_complete(
                _propose_follow_up(
                    {"experiment_id": "550e8400-e29b-41d4-a716-446655440000"},
                    org_id="org_A",
                )
            )

        titles = [o["title"] for o in result["options"]]
        assert "Re-test with Outlier Removal" in titles

    def test_follow_up_cross_org_blocked(self):
        """Cross-org experiment access should return error."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_exp = MagicMock()
        mock_exp.org_id = "org_B"

        with patch("resonantia.services.tool_executor.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_exp)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_session

            result = asyncio.get_event_loop().run_until_complete(
                _propose_follow_up(
                    {"experiment_id": "550e8400-e29b-41d4-a716-446655440000"},
                    org_id="org_A",
                )
            )

        assert "error" in result
        assert "not accessible" in result["error"]


class TestWorklistGeneration:
    def test_handler_registered(self):
        assert "generate_worklist" in TOOL_HANDLERS
        assert TOOL_HANDLERS["generate_worklist"] is _generate_worklist_tool

    @pytest.mark.asyncio
    async def test_missing_plate_map_id_returns_error(self):
        result = await _generate_worklist_tool({}, org_id="org_A")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_cross_org_plate_map_blocked(self):
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_pm = MagicMock()
        mock_pm.org_id = "org_B"

        with patch("resonantia.services.tool_executor.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_pm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_session

            result = await _generate_worklist_tool(
                {"plate_map_id": "550e8400-e29b-41d4-a716-446655440000"},
                org_id="org_A",
            )

        assert "error" in result
        assert "not accessible" in result["error"]
