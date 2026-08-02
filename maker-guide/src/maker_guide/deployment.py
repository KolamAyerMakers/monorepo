"""Deployment command and path defaults used by installed Maker Guide CLIs."""

from __future__ import annotations

from typing import Final

from maker_guide.config import DEFAULT_CONFIG_PATH

MAKER_GUIDE_DAEMON_USER: Final = "maker-guide"
MAKER_GUIDE_CREATE_LEARNER_COMMAND: Final = "/usr/local/bin/maker-guide-create-learner"
MAKER_GUIDE_INITIALIZE_LEARNER_COMMAND: Final = "/usr/local/bin/maker-guide-initialize-learner"
MAKER_GUIDE_REGISTRATION_COMMAND: Final = "/usr/local/bin/maker-guide-registration"
REFRESH_LEARNER_ROUTES_COMMAND: Final = "/usr/local/sbin/refresh-learner-routes"
REGISTRATION_STATE_FILE: Final = "/etc/maker-guide/registration-open"
LLDAP_CREATE_USER_COMMAND: Final = "/usr/local/sbin/lldap-create-user"
RUN_USER_COMMAND: Final = "/usr/sbin/runuser"
SUDO_COMMAND: Final = "/usr/bin/sudo"
CONFIGURATION_FILE: Final = str(DEFAULT_CONFIG_PATH)
