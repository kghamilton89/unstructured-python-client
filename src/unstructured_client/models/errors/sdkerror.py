"""Code generated by Speakeasy (https://speakeasyapi.dev). DO NOT EDIT."""

import requests as requests_http


class SDKError(Exception):
    """Represents an error returned by the API."""

    message: str
    status_code: int
    body: str
    raw_response: requests_http.Response

    def __init__(
        self,
        message: str,
        status_code: int,
        body: str,
        raw_response: requests_http.Response,
    ):
        self.message = message
        self.status_code = status_code
        self.body = body
        self.raw_response = raw_response

    def __str__(self):
        body = ""
        if len(self.body) > 0:
            body = f"\n{self.body}"

        return f"{self.message}: Status {self.status_code}{body}"
