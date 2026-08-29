# Troubleshooting

The failures people hit on a first run, with the error text they actually see. Search this page for the message you got.

Back to [the README](README.md), [Prerequisites](README.md#prerequisites), or the [30-second install](README.md#30-second-install).

## `edge-tts was not found on PATH.`

`skills/tts/scripts/render.py` checks for the `edge-tts` CLI before it starts rendering, so this appears immediately rather than partway through a multi-minute render:

```
edge-tts was not found on PATH.

Install it (it's separate from whatever Python runs this script):
    uv tool install "edge-tts>=7.2.8"
    pipx install "edge-tts>=7.2.8"
    pip install "edge-tts>=7.2.8"

Confirm with `edge-tts --version`. Requires Python 3.7+. https://pypi.org/project/edge-tts/
```

Fix: install it with whichever of the three you already have, then confirm.

```bash
uv tool install "edge-tts>=7.2.8"
edge-tts --version
```

If `edge-tts --version` still reports a missing command after a successful install, the install directory is not on your `PATH`. `uv tool update-shell` (or `pipx ensurepath`) adds it; open a new shell afterward, since an already-running shell keeps its old `PATH`. Full install notes are in [Prerequisites](README.md#prerequisites).

## `npm error code EBADENGINE` from `npx skills`

The `skills` CLI declares a Node floor in its `engines` field; check the current value with `npm view skills engines`. An older Node fails before anything installs, and npm prints:

```
npm error code EBADENGINE
npm error engine Unsupported engine
npm error engine Not compatible with your version of node/npm: skills@1.5.23
npm error notsup Not compatible with your version of node/npm: skills@1.5.23
npm error notsup Required: {"node":">=22.20.0"}
npm error notsup Actual:   {"node":"v18.20.4","npm":"10.7.0"}
```

The version, `Required`, and `Actual` values above are one example; yours report your own npm's view of the package and your installed Node.

Fix: check your version, then upgrade Node past the floor.

```bash
node --version
```

```bash
nvm install 22
nvm use 22
```

nvm-windows wants an exact version rather than a major: `nvm install 22.20.0`, then `nvm use 22.20.0`.

If you cannot upgrade Node, skip the CLI entirely: [No Node?](README.md#no-node) covers cloning the repo and copying the skill folders in by hand.

## `python3` on Windows, and `.venv/bin` versus `.venv/Scripts`

`python3` is the interpreter name on macOS and Linux. On Windows it usually resolves to a Microsoft Store app-execution alias that installs nothing and runs nothing. Running `python3` there prints something close to:

```
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Manage App Execution Aliases.
```

The exact wording varies by Windows build.

Windows virtual environments also put executables in `Scripts`, not `bin`, so running the bash/zsh block from [Development](README.md#development) instead of the PowerShell one next to it fails with:

```
.venv/bin/pip: The term '.venv/bin/pip' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
```

That is PowerShell 7's wording. Windows PowerShell 5.1 says "as the name of a cmdlet, function, script file, or operable program" instead, so search for the path rather than the full sentence.

Fix: use `python` or `py -3`, and the `Scripts` path.

```powershell
py -3 -m venv .venv
.venv/Scripts/pip install pytest ruff
.venv/Scripts/python -m pytest
```

## `edge-tts failed to render.`

`render.py` catches a non-zero exit from the engine and reports:

```
edge-tts failed to render. This can happen when a sandboxed shell blocks the network call edge-tts makes (some agent harnesses do this).
Run the command yourself in a regular terminal:
```

It then prints the exact `edge-tts` command it tried. Fix: copy that command into a normal terminal outside the agent and run it there. `edge-tts` reaches a Microsoft speech endpoint over the network, so it cannot work in a shell with no outbound access.

## `CERTIFICATE_VERIFY_FAILED` when `edge-tts` connects

On a machine where a corporate proxy, network filter, or antivirus product intercepts TLS, `edge-tts` cannot verify the certificate presented for the Microsoft speech endpoint and fails with Python's standard SSL error:

```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

The interceptor signs traffic with its own root certificate, and verification fails when that root is missing from the certificate store Python checks against. Fix: export the interceptor's root from your system certificate store, append it to a PEM bundle, and point Python at that bundle with `SSL_CERT_FILE`. Python's `ssl` module reads that variable, so it applies to `edge-tts` too; `python3 -c "import ssl; print(ssl.get_default_verify_paths())"` prints the paths currently in effect.

```bash
export SSL_CERT_FILE=/path/to/bundle-with-corporate-root.pem
```

```powershell
$env:SSL_CERT_FILE = "C:/path/to/bundle-with-corporate-root.pem"
```

Do not disable certificate verification as a workaround. If the interception is not something you control, render on a machine outside that network, or pick a different engine from [`skills/tts/README.md`](skills/tts/README.md#requirements-and-choosing-a-tts-engine).

## Something else

Open an issue: <https://github.com/ArunskiOrg/BenArunskiUtils/issues>. Include the command you ran and the full error text.
