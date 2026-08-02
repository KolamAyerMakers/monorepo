"""Pure learner identity policy applied by infra provisioning helpers."""

from __future__ import annotations

import re
from typing import Final

HANDLE_PATTERN_TEXT: Final = r"^[a-z][a-z0-9-]{1,31}$"
HANDLE_PATTERN: Final = re.compile(HANDLE_PATTERN_TEXT)
DEFAULT_PRIMARY_GROUP: Final = "humans"
DEFAULT_SECONDARY_GROUPS: Final = ("linux-foundations",)
MANAGED_UID_MINIMUM: Final = 10_000
LEARNER_UID_MINIMUM: Final = 20_000
LEARNER_UID_MAXIMUM: Final = 20_999
DEFAULT_LOGIN_SHELL: Final = "/bin/bash"
HOME_DIRECTORY_PREFIX: Final = "/home"


def is_managed_uid(uid: int) -> bool:
    """Return whether a UID belongs to a managed classroom identity."""
    return MANAGED_UID_MINIMUM <= uid <= LEARNER_UID_MAXIMUM


def is_learner_uid(uid: int) -> bool:
    """Return whether a UID belongs to an LLDAP-allocated learner."""
    return LEARNER_UID_MINIMUM <= uid <= LEARNER_UID_MAXIMUM
