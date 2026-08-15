# VM Bridge

A GitHub Actions bridge for a network-restricted VM.

## Architecture

`restricted VM -> GitHub repository -> GitHub Actions (Internet) -> artifact -> GitHub connector -> /mnt/data`

The VM itself stays isolated. Network-required work runs on a GitHub-hosted runner and returns as an Actions artifact.

## Supported jobs

- `http_get`: fetch a small public HTTP(S) response.
- `download`: download a public file and return it as an artifact.
- `npm_pack`: download an npm package tarball.
- `pip_download`: download Python wheels/sdists.
- `deepseek_chat`: make a non-streaming DeepSeek request using the repository secret `DEEPSEEK_API_KEY`.

## Security

Do not put API keys in source files or job JSON. Use GitHub Actions secrets. This bridge intentionally does not expose arbitrary shell execution.

## Limitation

This is a batch/file bridge, not a VPN or real-time proxy. It is suitable for downloads, builds and API jobs, but not token-by-token streaming or a permanent tunnel.
