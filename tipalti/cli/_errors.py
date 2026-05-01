"""AfiError and exit-code policy (stable-contract — copy verbatim).

Every failure inside tipalti raises :class:`AfiError`. The CLI entry
point catches it and exits with :attr:`AfiError.code`. Guarantees:

* no Python traceback leaks to stderr;
* every error has shape ``{code, message, remediation}``;
* the exit-code policy is centralised.
"""

from __future__ import annotations

from dataclasses import dataclass

# Exit-code policy (documented in ``tipalti learn`` output).
# 0  = success
# 1  = user-input error (bad flag, bad path, missing arg)
# 2  = environment / setup error
# 3+ = reserved
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_ENV_ERROR = 2


@dataclass
class AfiError(Exception):
    """Structured error with a remediation hint for agents.

    ``kind`` is a free-form discriminator string (e.g. ``"missing_creds"``)
    that lets handlers distinguish between errors sharing the same exit
    code without parsing ``message``. Optional; defaults to empty.
    """

    code: int
    message: str
    remediation: str = ""
    kind: str = ""

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
        }
        if self.kind:
            payload["kind"] = self.kind
        return payload
