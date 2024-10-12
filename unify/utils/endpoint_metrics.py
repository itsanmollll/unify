import datetime
import requests
from typing import Optional, Union, Dict

from unify import BASE_URL
from .helpers import _validate_api_key
from unify.types import _FormattedBaseModel


class Metrics(_FormattedBaseModel):
    time_to_first_token: float
    inter_token_latency: float
    input_cost: float
    output_cost: float
    measured_at: Union[datetime.datetime, str]
    region:str
    seq_len: str


def get_endpoint_metrics(
    endpoint: str,
    region: str = "Iowa",
    seq_len: str = "short",
    start_time: Optional[Union[datetime.datetime, str]] = None,
    end_time: Optional[Union[datetime.datetime, str]] = None,
    api_key: Optional[str] = None,
) -> Metrics:
    """
    Retrieve the set of cost and speed metrics for the specified endpoint.

    Args:
        endpoint: The endpoint to retrieve the metrics for, in model@provider format

        region: Region where the benchmark is run. Options are: "Belgium", "Hong Kong"
        or "Iowa".

        seq_len: Length of the sequence used for benchmarking, can be short or long.

        start_time: Window start time. Only returns the latest benchmark if unspecified.

        end_time: Window end time. Assumed to be the current time if this is unspecified
        and start_time is specified. Only the latest benchmark is returned if both are
        unspecified.

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
        "provider": endpoint.split("@")[1],
        "region": region,
        "seq_len": seq_len,
        "start_time": start_time,
        "end_time": end_time,
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
        measured_at=metrics_dct["measured_at"],
        region=region,
        seq_len=seq_len,
    )


def log_endpoint_metric(
        endpoint_name: str,
        metric_name: str,
        value: float,
        measured_at: Optional[Union[str, datetime.datetime]] = None,
        api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Append speed or cost data to the standardized time-series benchmarks for a custom
    endpoint (only custom endpoints are publishable by end users).

    Args:
        endpoint_name: Name of the custom endpoint to append benchmark data for.

        metric_name: Name of the metric to submit. Allowed metrics are: “input-cost”,
        “output-cost”, “time-to-first-token”, “inter-token-latency”.

        value: Value of the metric to submit.

        measured_at: The timestamp to associate with the submission. Defaults to current
        time if unspecified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {
        "endpoint_name": endpoint_name,
        "metric_name": metric_name,
        "value": value,
        "measured_at": measured_at,
    }
    response = requests.get(
        BASE_URL + "/endpoint-metrics",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()
