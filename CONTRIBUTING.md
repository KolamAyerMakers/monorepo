# Contributing

Open an issue before proposing a large change. Keep changes focused, retain tests for behavior changes, and run the relevant subproject checks through the configured Git hooks.

Do not commit credentials, private keys, decrypted pillar data, generated Maker Guide artifacts, or runtime data. Pulumi encrypted values and Age-encrypted pillar values are configuration and remain tracked.

Infrastructure changes require a maintainer to review and apply them manually. CI must not contact production services, decrypt secrets, run Salt remotely, or run `pulumi up`.
