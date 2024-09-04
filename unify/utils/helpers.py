import os
import json
import requests
from typing import List, Dict, Optional, Union, Any


def _res_to_list(response: requests.Response) -> Union[List, Dict]:
    return json.loads(response.text)


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


def _default(value: Any, default_value: Any) -> Any:
    return value if value is not None else default_value
