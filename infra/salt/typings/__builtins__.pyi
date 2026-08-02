from typing import Any, Callable

# __salt__ is typically a dictionary of all the Salt execution modules available
# (functions).
__salt__: dict[str, Callable[..., Any]]  # pyright: ignore[reportExplicitAny]

# The __grains__ dictionary contains the grains data which provides static
# information about the system.
__grains__: dict[str, Any]  # pyright: ignore[reportExplicitAny]

# __states__ is a dictionary of all the Salt state modules available (functions).
# Only available within custom state modules (_states/).
__states__: dict[str, Callable[..., Any]]  # pyright: ignore[reportExplicitAny]

# __opts__ is the Salt minion/master configuration dictionary.
__opts__: dict[str, Any]  # pyright: ignore[reportExplicitAny]
