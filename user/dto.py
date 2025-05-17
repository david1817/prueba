from dataclasses import dataclass
from typing import Any

@dataclass
class ResponseData:
    code: int
    message: str
    data: Any

def response_data_to_dict(response_data: ResponseData) -> dict:
    return {
        'code': response_data.code,
        'message': response_data.message,
        'data': response_data.data,
    }