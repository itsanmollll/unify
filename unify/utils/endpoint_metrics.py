from datetime import datetime

import requests
from typing import Optional

from unify import BASE_URL
from .helpers import _validate_api_key
from unify.types import _FormattedBaseModel


class Metrics(_FormattedBaseModel):
    time_to_first_token: float
    inter_token_latency: float
    input_cost: float
    output_cost: float
    measured_at: str


def get_endpoint_metrics(
    endpoint: str,
    api_key: Optional[str] = None,
) -> Metrics:
    """
    Retrieve the set of cost and speed metrics for the specified endpoint.

    Args:
        endpoint: The endpoint to retrieve the metrics for, in model@provider format

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The set of metrics for the specified endpoint.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {
        "model": endpoint.split("@")[0],
        "provider": endpoint.split("@")[1]
    }
    response = requests.get(
        BASE_URL + "/endpoint-metrics",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    metrics_dct = response.json()[0]
    return Metrics(
        time_to_first_token=metrics_dct["ttft"],
        inter_token_latency=metrics_dct["itl"],
        input_cost=metrics_dct["input_cost"],
        output_cost=metrics_dct["output_cost"],
        measured_at=metrics_dct["measured_at"]
    )
