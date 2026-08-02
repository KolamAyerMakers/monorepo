#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class BulkCommand:
    parts: list[bytes]


@dataclass(frozen=True, slots=True)
class ManagedChannel:
    name: str
    operators: tuple[str, ...] = ()


class DatabaseParseError(ValueError):
    pass


def _read_line(content: bytes, offset: int) -> tuple[bytes, int]:
    end_offset = content.find(b"\r\n", offset)
    if end_offset == -1:
        raise DatabaseParseError("unterminated line")
    return content[offset:end_offset], end_offset + 2


def _read_bulk_string(content: bytes, offset: int) -> tuple[bytes, int]:
    length_line, offset = _read_line(content, offset)
    if not length_line.startswith(b"$"):
        raise DatabaseParseError("expected bulk string length")
    try:
        length = int(length_line[1:])
    except ValueError as error:
        raise DatabaseParseError("invalid bulk string length") from error
    value = content[offset : offset + length]
    next_offset = offset + length
    if content[next_offset : next_offset + 2] != b"\r\n":
        raise DatabaseParseError("unterminated bulk string")
    return value, next_offset + 2


def _read_command(content: bytes, offset: int) -> tuple[BulkCommand, int]:
    count_line, offset = _read_line(content, offset)
    if not count_line.startswith(b"*"):
        raise DatabaseParseError("expected command array")
    try:
        count = int(count_line[1:])
    except ValueError as error:
        raise DatabaseParseError("invalid command array length") from error
    parts: list[bytes] = []
    while len(parts) < count:
        part, offset = _read_bulk_string(content, offset)
        parts.append(part)
    return BulkCommand(parts), offset


def _load_records(database_file: Path) -> dict[str, str]:
    if not database_file.exists():
        return {}
    content = database_file.read_bytes()
    offset = 0
    records: dict[str, str] = {}
    while offset < len(content):
        command, offset = _read_command(content, offset)
        if not command.parts:
            continue
        operation = command.parts[0].lower()
        if operation == b"set" and len(command.parts) >= 3:
            records[command.parts[1].decode()] = command.parts[2].decode()
        elif operation == b"del" and len(command.parts) >= 2:
            _ = records.pop(command.parts[1].decode(), None)
    return records


def _registered_channels(
    records: dict[str, str],
) -> dict[str, tuple[str, dict[str, object]]]:
    channels: dict[str, tuple[str, dict[str, object]]] = {}
    for key, value in records.items():
        if not key.startswith("1 "):
            continue
        try:
            channel = cast(object, json.loads(value))
        except json.JSONDecodeError:
            continue
        if not isinstance(channel, dict):
            continue
        channel_record = cast(dict[str, object], cast(dict[object, object], channel))
        name = channel_record.get("Name")
        if isinstance(name, str):
            channels[name.casefold()] = (key, channel_record)
    return channels


def _uuid() -> str:
    return base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _channel_record(channel: ManagedChannel, founder: str, channel_uuid: str) -> str:
    account_to_umode: dict[str, int] = {founder: ord("q")}
    for operator in channel.operators:
        if operator.casefold() != founder.casefold():
            account_to_umode[operator] = ord("o")
    return json.dumps(
        {
            "Name": channel.name,
            "UUID": channel_uuid,
            "RegisteredAt": _timestamp(),
            "Founder": founder,
            "Modes": [ord("n"), ord("t"), ord("C")],
            "AccountToUMode": account_to_umode,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _bulk(value: bytes) -> bytes:
    return b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n"


def _set_command(key: str, value: str) -> bytes:
    return b"*3\r\n" + _bulk(b"set") + _bulk(key.encode()) + _bulk(value.encode())


def _channel_from_value(value: object) -> ManagedChannel:
    if isinstance(value, str):
        return ManagedChannel(value)
    if not isinstance(value, dict):
        raise ValueError("channels file entries must be strings or channel mappings")
    channel = cast(dict[str, object], cast(dict[object, object], value))
    name = channel.get("name")
    operators = channel.get("operators", [])
    if not isinstance(name, str) or not isinstance(operators, list):
        raise ValueError("channel mappings require string name and list operators")
    if not all(isinstance(operator, str) for operator in cast(list[object], operators)):
        raise ValueError("channel operators must be strings")
    return ManagedChannel(name, tuple(cast(list[str], operators)))


def _channels_from_file(channels_file: Path) -> list[ManagedChannel]:
    channels = cast(object, json.loads(channels_file.read_text(encoding="utf-8")))
    if not isinstance(channels, list):
        raise ValueError("channels file must contain a JSON list")
    resolved_channels: list[ManagedChannel] = []
    for channel in cast(list[object], channels):
        resolved_channels.append(_channel_from_value(channel))
    return resolved_channels


def _resolve_channels(
    channel_arguments: Sequence[str] | None,
    channels_file: Path | None,
) -> list[ManagedChannel]:
    channels = [ManagedChannel(name) for name in channel_arguments or []]
    if channels_file is not None:
        channels.extend(_channels_from_file(channels_file))
    if not channels:
        raise ValueError("at least one --channel or --channels-file entry is required")
    return channels


def _updated_channel_record(
    channel: ManagedChannel,
    existing_channel: dict[str, object],
) -> str | None:
    account_to_umode = existing_channel.get("AccountToUMode")
    updated_account_to_umode = (
        dict(cast(dict[str, object], account_to_umode))
        if isinstance(account_to_umode, dict)
        else {}
    )
    existing_accounts = {
        account.casefold(): account for account in updated_account_to_umode
    }
    for operator in channel.operators:
        account = existing_accounts.get(operator.casefold(), operator)
        if updated_account_to_umode.get(account) != ord("o"):
            updated_account_to_umode[account] = ord("o")
    if updated_account_to_umode == account_to_umode:
        return None
    updated_channel = dict(existing_channel)
    updated_channel["AccountToUMode"] = updated_account_to_umode
    return json.dumps(updated_channel, separators=(",", ":"), sort_keys=True)


def _pending_channels(
    database_file: Path,
    channels: Sequence[ManagedChannel],
) -> list[ManagedChannel]:
    registered_channels = _registered_channels(_load_records(database_file))
    pending_channels: list[ManagedChannel] = []
    for channel in channels:
        existing_channel = registered_channels.get(channel.name.casefold())
        if (
            existing_channel is None
            or _updated_channel_record(channel, existing_channel[1]) is not None
        ):
            pending_channels.append(channel)
    return pending_channels


def ensure_channels(
    database_file: Path,
    founder: str,
    channels: Sequence[object],
) -> int:
    resolved_channels = [
        channel if isinstance(channel, ManagedChannel) else _channel_from_value(channel)
        for channel in channels
    ]
    pending_channels = _pending_channels(database_file, resolved_channels)
    if not pending_channels:
        return 0
    registered_channels = _registered_channels(_load_records(database_file))
    with database_file.open("ab") as database:
        for channel in pending_channels:
            existing_channel = registered_channels.get(channel.name.casefold())
            if existing_channel is None:
                channel_uuid = _uuid()
                record_key = f"1 {channel_uuid}"
                channel_record = _channel_record(channel, founder, channel_uuid)
            else:
                record_key, existing_record = existing_channel
                channel_record = _updated_channel_record(channel, existing_record)
                if channel_record is None:
                    continue
            _ = database.write(
                _set_command(
                    record_key,
                    channel_record,
                )
            )
    return len(pending_channels)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--database", required=True, type=Path)
    _ = parser.add_argument("--founder", required=True)
    _ = parser.add_argument("--channel", action="append", dest="channels")
    _ = parser.add_argument("--channels-file", type=Path)
    _ = parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    arguments = _argument_parser().parse_args()
    channels = _resolve_channels(arguments.channels, arguments.channels_file)
    pending_channels = _pending_channels(arguments.database, channels)
    if arguments.check:
        return 1 if pending_channels else 0
    _ = ensure_channels(arguments.database, arguments.founder, channels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
