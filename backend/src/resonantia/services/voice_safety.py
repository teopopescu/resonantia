"""Voice safety filter — restricts which tools can be triggered via voice.

Voice commands should be limited to safe, read-only operations.
Destructive or consequential actions must redirect to text confirmation.
"""

from __future__ import annotations

VOICE_SAFE_TOOLS: frozenset[str] = frozenset({
    "lookup_sample",
    "check_inventory",
    "get_expiring_samples",
    "get_sample_stats",
    "query_experiments",
    "query_eln_entries",
    "query_protocols",
    "query_plate_maps",
    "calculate_dilution",
    "get_ic50_values",
    "read_file_contents",
    "get_file_info",
    "list_files",
    "get_plate_map_details",
    "fit_dose_response",
    "normalize_plate",
    "calculate_z_prime",
    "qpcr_analysis",
    "get_processing_results",
})

VOICE_BLOCKED_TOOLS: frozenset[str] = frozenset({
    "create_eln_entry",
    "submit_eln_entry",
    "create_plate_map",
    "create_protocol",
    "generate_worklist",
    "cherry_pick",
    "serial_dilution",
    "create_experiment",
    "propose_follow_up_experiment",
    "design_next_experiment",
    "add_sample",
})

VOICE_REDIRECT_MESSAGE = (
    "This action requires text confirmation. "
    "I've noted your request — please confirm in the chat interface."
)


def is_voice_safe(tool_name: str) -> bool:
    if tool_name in VOICE_SAFE_TOOLS:
        return True
    if tool_name in VOICE_BLOCKED_TOOLS:
        return False
    return False


def voice_block_message(tool_name: str) -> str:
    return (
        f"The tool '{tool_name}' cannot be executed via voice. "
        f"{VOICE_REDIRECT_MESSAGE}"
    )
