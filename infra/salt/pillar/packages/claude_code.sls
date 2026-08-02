packages:
  claude_code:
    version: 2.1.212
    arch:
      x86_64:
        libc: static
        url: https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/{version}/linux-x64/claude
        checksum: sha256=044a88cf3a5180776617fd3da1238dcbf9141ddec449a39cf7d2af1ac78e684e
      aarch64:
        libc: static
        url: https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/{version}/linux-arm64/claude
        checksum: sha256=66e88634a8573a002702e6a9de0d80cb9bb7c9072f9e6f4486778539057dfd3c
    scope: system
    binaries:
      claude: claude_code
