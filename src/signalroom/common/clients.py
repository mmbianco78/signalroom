"""Client configuration for multi-client support.

Critical Ads serves multiple clients. This module provides simple client
tagging without full multi-tenancy. Data is tagged with client_id for
grouping in analytics.

Current clients:
- 713: [Description TBD]
- CTI: ClayTargetInstruction
"""

from dataclasses import dataclass


@dataclass
class ClientConfig:
    """Configuration for a client."""

    id: str
    name: str
    sources: list[str]  # Which sources this client uses


# Client registry
CLIENTS: dict[str, ClientConfig] = {
    "713": ClientConfig(
        id="713",
        name="713",
        sources=[],  # Configure as needed
    ),
    "cti": ClientConfig(
        id="cti",
        name="ClayTargetInstruction",
        sources=[],  # Configure as needed
    ),
}


def get_client(client_id: str) -> ClientConfig:
    """Get client configuration by ID.

    Args:
        client_id: Client identifier.

    Returns:
        Client configuration.

    Raises:
        KeyError: If client not found.
    """
    if client_id not in CLIENTS:
        raise KeyError(f"Unknown client: {client_id}. Available: {list(CLIENTS.keys())}")
    return CLIENTS[client_id]


def get_sources_for_client(client_id: str) -> list[str]:
    """Get list of sources configured for a client.

    Args:
        client_id: Client identifier.

    Returns:
        List of source names.
    """
    return get_client(client_id).sources
