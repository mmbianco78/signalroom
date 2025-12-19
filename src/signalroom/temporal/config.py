"""Temporal client configuration and retry policies."""

from datetime import timedelta

from temporalio.client import Client, TLSConfig
from temporalio.common import RetryPolicy

from signalroom.common import settings

# Default retry policy for activities
RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=5,
    non_retryable_error_types=[
        "ValueError",  # Bad input, retrying won't help
        "KeyError",  # Missing required data
    ],
)

# Retry policy for browser/slow activities
BROWSER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=10),
    maximum_attempts=3,
)


async def get_temporal_client() -> Client:
    """Create and return a Temporal client.

    Handles both local development (no TLS) and Temporal Cloud (with API key or mTLS).

    Returns:
        Connected Temporal client.
    """
    api_key = settings.temporal_api_key.get_secret_value()

    # Temporal Cloud with API key (preferred)
    if api_key:
        return await Client.connect(
            settings.temporal_address,
            namespace=settings.temporal_namespace,
            api_key=api_key,
            tls=True,  # Temporal Cloud requires TLS
        )

    # Temporal Cloud with mTLS certificates (legacy)
    if settings.temporal_tls_cert_path and settings.temporal_tls_key_path:
        with open(settings.temporal_tls_cert_path, "rb") as f:
            client_cert = f.read()
        with open(settings.temporal_tls_key_path, "rb") as f:
            client_key = f.read()

        tls_config = TLSConfig(
            client_cert=client_cert,
            client_private_key=client_key,
        )

        return await Client.connect(
            settings.temporal_address,
            namespace=settings.temporal_namespace,
            tls=tls_config,
        )

    # Local development (no TLS)
    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )
