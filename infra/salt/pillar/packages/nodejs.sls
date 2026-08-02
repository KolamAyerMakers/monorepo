packages:
  nodejs:
    version: 24.14.1
    arch:
      x86_64:
        url: https://nodejs.org/dist/v{version}/node-v{version}-linux-x64.tar.gz
        checksum: sha256=ace9fa104992ed0829642629c46ca7bd7fd6e76278cb96c958c4b387d29658ea
      aarch64:
        url: https://nodejs.org/dist/v{version}/node-v{version}-linux-arm64.tar.gz
        checksum: sha256=734ff04fa7f8ed2e8a78d40cacf5ac3fc4515dac2858757cbab313eb483ba8a2
    command_download: true
    scope: system
    binaries:
      - node
      - npm
      - npx
      - corepack
    bin_subdir: bin
    strip_components: 1
    npm_global_packages:
      opencode-ai:
        version: 1.18.3
        integrity: sha512-HnItl/+uhSpj7JV9x6ITiE0XFq4b/PKF5OM03TIyiFoFiLw3MQoJOAXZFTEzC7IOgAIYcysRQBBmCmlXILkxww==
        binaries:
          - opencode
      "@openai/codex":
        version: 0.144.5
        integrity: sha512-jjB+K+OMv572mKhS+2QuLxWXDJNdpwbPenf+V+8bdq7wg4Scqt3cn6WEekD8wPqDVZqck0HSX17K9rD9kbDJQA==
        binaries:
          - codex
      tldr:
        version: 3.5.0
        integrity: sha512-1WtgsrQMKdW1OnAO/ET/8+WIY72a89vb1BI/bj7mtlBwakfIilqPneU/ZpxhZjI+onFlwI3sTzA71VhNlvP8/g==
        binaries:
          - tldr
