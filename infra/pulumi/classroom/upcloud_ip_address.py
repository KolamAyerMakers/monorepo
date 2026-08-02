"""UpCloud IP address reverse DNS integration for the Pulumi stack."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pulumi
from pulumi import dynamic

_UPCLOUD_API_BASE_URL = "https://api.upcloud.com/1.3"
_UPCLOUD_REQUEST_TIMEOUT_SECONDS = 30.0


class UpCloudIpAddressError(RuntimeError):
    """Raised when UpCloud rejects an IP address API request."""


@dataclass(frozen=True, slots=True)
class UpCloudIpAddressReverseDnsRecord:
    """UpCloud IP address reverse DNS state."""

    ip_address: str
    reverse_dns_hostname: str


class _HTTPResponse(Protocol):
    def read(self) -> bytes: ...

    def getcode(self) -> int: ...


_RequestOpener = Callable[[Request, float], _HTTPResponse]


def _default_request_opener(request: Request, timeout: float) -> _HTTPResponse:
    return cast(_HTTPResponse, urlopen(request, timeout=timeout))


def _decode_json_response(response: _HTTPResponse) -> object:
    response_body = response.read().decode()
    try:
        return json.loads(response_body)
    except json.JSONDecodeError as error:
        raise UpCloudIpAddressError("UpCloud returned malformed JSON") from error


def _require_response_mapping(
    response: object,
    description: str,
) -> Mapping[str, object]:
    if not isinstance(response, dict):
        raise UpCloudIpAddressError(
            f"UpCloud returned a non-object {description} response"
        )
    return response


def _read_required_string(
    values: Mapping[str, object],
    key: str,
    *,
    allow_empty: bool = False,
) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise UpCloudIpAddressError(
            f"UpCloud response field {key!r} is missing or not a string"
        )

    if not allow_empty and value == "":
        raise UpCloudIpAddressError(f"UpCloud response field {key!r} is empty")

    return value


def _parse_reverse_dns_record(
    values: Mapping[str, object],
) -> UpCloudIpAddressReverseDnsRecord:
    ip_address = _require_response_mapping(values.get("ip_address"), "ip_address")
    return UpCloudIpAddressReverseDnsRecord(
        ip_address=_read_required_string(ip_address, "address"),
        reverse_dns_hostname=_read_required_string(
            ip_address,
            "ptr_record",
            allow_empty=True,
        ),
    )


class UpCloudIpAddressClient:
    """Small UpCloud IP address API client."""

    def __init__(
        self,
        *,
        token: str,
        request_opener: _RequestOpener = _default_request_opener,
    ) -> None:
        self._token = token
        self._request_opener = request_opener

    def read_reverse_dns_record(
        self,
        ip_address: str,
    ) -> UpCloudIpAddressReverseDnsRecord:
        return _parse_reverse_dns_record(
            _require_response_mapping(
                self._request(method="GET", ip_address=ip_address),
                "IP address",
            )
        )

    def update_reverse_dns_record(
        self,
        *,
        ip_address: str,
        reverse_dns_hostname: str,
    ) -> UpCloudIpAddressReverseDnsRecord:
        return _parse_reverse_dns_record(
            _require_response_mapping(
                self._request(
                    method="PATCH",
                    ip_address=ip_address,
                    request_body={"ip_address": {"ptr_record": reverse_dns_hostname}},
                ),
                "IP address",
            )
        )

    def _request(
        self,
        *,
        method: str,
        ip_address: str,
        request_body: Mapping[str, object] | None = None,
    ) -> object:
        request_data = (
            json.dumps(request_body).encode() if request_body is not None else None
        )
        request_path = f"/ip_address/{ip_address}"
        request = Request(
            url=f"{_UPCLOUD_API_BASE_URL}{request_path}",
            data=request_data,
            method=method,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
        )
        return _decode_json_response(self._send_request(request, method, request_path))

    def _send_request(
        self,
        request: Request,
        method: str,
        path: str,
    ) -> _HTTPResponse:
        try:
            response = self._request_opener(request, _UPCLOUD_REQUEST_TIMEOUT_SECONDS)
        except HTTPError as error:
            response_body = error.read().decode(errors="replace")
            raise UpCloudIpAddressError(
                f"UpCloud {method} {path} failed with HTTP {error.code}: "
                f"{response_body}"
            ) from error
        except URLError as error:
            raise UpCloudIpAddressError(
                f"UpCloud {method} {path} failed: {error.reason}"
            ) from error

        response_status = response.getcode()
        if response_status < 200 or response_status >= 300:
            raise UpCloudIpAddressError(
                f"UpCloud {method} {path} failed with HTTP {response_status}"
            )
        return response


def _input_string(properties: Mapping[str, object], key: str) -> str:
    value = properties.get(key)
    if not isinstance(value, str) or value == "":
        raise UpCloudIpAddressError(f"{key}: expected a non-empty string")
    return value


def _reverse_dns_outputs(
    properties: Mapping[str, object],
    record: UpCloudIpAddressReverseDnsRecord,
) -> dict[str, object]:
    return {
        **properties,
        "ip_address": record.ip_address,
        "reverse_dns_hostname": record.reverse_dns_hostname,
    }


class _UpCloudIpAddressReverseDnsProvider(dynamic.ResourceProvider):
    def diff(
        self,
        _id: str,
        olds: dict[str, object],
        news: dict[str, object],
    ) -> dynamic.DiffResult:
        return dynamic.DiffResult(
            changes=any(
                olds.get(key) != news.get(key)
                for key in ("token", "ip_address", "reverse_dns_hostname")
            )
        )

    def create(self, props: dict[str, object]) -> dynamic.CreateResult:
        record = self._update_reverse_dns_record(props)
        return dynamic.CreateResult(
            record.ip_address,
            _reverse_dns_outputs(props, record),
        )

    def read(
        self,
        id_: str,
        props: dict[str, object],
    ) -> dynamic.ReadResult:
        client = UpCloudIpAddressClient(token=_input_string(props, "token"))
        record = client.read_reverse_dns_record(_input_string(props, "ip_address"))
        return dynamic.ReadResult(id_, _reverse_dns_outputs(props, record), props)

    def update(
        self,
        _id: str,
        _olds: dict[str, object],
        news: dict[str, object],
    ) -> dynamic.UpdateResult:
        record = self._update_reverse_dns_record(news)
        return dynamic.UpdateResult(_reverse_dns_outputs(news, record))

    def delete(self, _id: str, _properties: dict[str, object]) -> None:
        return None

    def _update_reverse_dns_record(
        self,
        properties: Mapping[str, object],
    ) -> UpCloudIpAddressReverseDnsRecord:
        client = UpCloudIpAddressClient(token=_input_string(properties, "token"))
        return client.update_reverse_dns_record(
            ip_address=_input_string(properties, "ip_address"),
            reverse_dns_hostname=_input_string(properties, "reverse_dns_hostname"),
        )


class UpCloudIpAddressReverseDns(pulumi.dynamic.Resource):
    """Manage a PTR record for an existing UpCloud IP address."""

    def __init__(
        self,
        name: str,
        *,
        token: pulumi.Input[str],
        ip_address: pulumi.Input[str],
        reverse_dns_hostname: pulumi.Input[str],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(
            _UpCloudIpAddressReverseDnsProvider(),
            name,
            {
                "token": token,
                "ip_address": ip_address,
                "reverse_dns_hostname": reverse_dns_hostname,
            },
            opts,
        )
