<h1 align="center">AION Flow</h1>
<p align="center"><strong><em>AI-Based Standard Cells Generation</em></strong></p>

## Quick start

Set up the environment:

```bash
source env.sh
```

Run the full cluster-extraction flow:

```bash
make aion-opt-run-all
```

Outputs land under `build/aion_opt/` by default. Use `BUILD_DIR=` to redirect:

```bash
make aion-opt-run-all BUILD_DIR=build/pm32
```

Or drive it from a YAML config:

```bash
make aion-opt-run-all CONFIG=examples/aion_opt/aion_opt.yaml BUILD_DIR=build/pm32
```

## Running the EDA docker container

The Makefile targets above (and the `./run.sh`-style wrappers used by
companion repos such as `SG13G2_ASIC-Design-FLL`) expect the open-source
EDA tools (Xschem, Magic, KLayout, ngspice, Yosys, OpenROAD, OpenSTA,
Netgen, LibreLane, cocotb, ...) to be running inside a docker/podman
container built from the `hpretl/iic-osic-tools` image. `start_local.sh`
starts (or resumes) that container for you.

**Nothing is hardcoded** — you tell the script, on the command line, which
folders on your machine should be visible inside the container. Nothing
outside the folders you pass is visible to the tools running inside it.

### The 2-minute version

First, check whether you already have the image pulled, and note its tag
(`start_local.sh` defaults to `latest`, which you may not have):

```bash
docker images | grep iic-osic-tools
```

From this repo, mount this repo itself plus any other design repo you're
working with (e.g. a sibling checkout of `SG13G2_ASIC-Design-FLL`), and
pass `--tag` with whatever tag `docker images` showed above (skip `--tag`
only if you don't have the image yet and are OK pulling `latest`):

```bash
./start_local.sh \
    --tag 2026.05 \
    --mount "$(pwd)" \
    --mount ../SG13G2_ASIC-Design-FLL
```

Without a matching `--tag`, Docker will pull `hpretl/iic-osic-tools:latest`
from scratch (several GB) even if you already have another tag locally —
see [Already have the image, or a container running?](#already-have-the-image-or-a-container-running)
for more on this.

This opens an interactive shell inside the container. Each `--mount PATH`
shows up inside the container at `/foss/designs/<basename of PATH>` — so
the two commands above land at `/foss/designs/aion_flow` and
`/foss/designs/SG13G2_ASIC-Design-FLL` respectively. That layout matters:
tooling inside those repos (e.g. `SG13G2_ASIC-Design-FLL`'s `run.sh` /
`CLAUDE.md`) assumes the repo is reachable under `/foss/designs/<repo
name>`, and `scripts/docker_run.sh` in this repo assumes this repo is at
`/foss/designs/aion_flow` — so mount each repo by its own directory
(don't rename it) unless you know a tool needs a different name.

Once you're done, exit the shell; the container keeps running in the
background. Run `./start_local.sh` again (no need to repeat `--mount`
unless you want to change what's mounted for the *next* fresh container)
to reattach, or to be prompted to stop/remove it.

### Mounting more than one repo

Pass `--mount` once per repo/folder you want visible inside the
container. You can rename how a repo appears inside the container with
`--mount HOST_PATH:name`:

```bash
./start_local.sh \
    --mount "$(pwd)" \
    --mount ../SG13G2_ASIC-Design-FLL \
    --mount ~/phd/aion/aion_chip \
    --mount ~/phd/trash/SynapTick:SynapTick
```

If you forget `--mount` entirely, the container still starts, but only an
empty base directory is visible inside it — the script prints a warning
reminding you to add `--mount` flags.

### All options

```bash
./start_local.sh --help
```

Key flags:

| Flag | Purpose | Default |
|------|---------|---------|
| `--mount HOST[:NAME]` | Bind-mount `HOST` at `/foss/designs/NAME` (repeatable) | — (none) |
| `--designs-dir DIR` | Base dir mounted at `/foss/designs` | `$HOME/eda/designs` |
| `--docker-user NAME` | Docker Hub user/org for the image | `hpretl` |
| `--image NAME` | Image name | `iic-osic-tools` |
| `--tag TAG` | Image tag | `latest` |
| `--registry REGISTRY` | Registry prefix (`""` for unqualified names) | `docker.io` |
| `--engine docker\|podman` | Container engine | auto-detected |
| `--name NAME` | Container name | `iic-osic-tools_shell_uid_<your uid>` |

Every flag also has a matching environment variable (`DOCKER_USER`,
`DOCKER_IMAGE`, `DOCKER_TAG`, `DOCKER_REGISTRY`, `CONTAINER_ENGINE`,
`CONTAINER_NAME`, `CONTAINER_USER`, `CONTAINER_GROUP`, `DESIGNS`) if you
prefer to `export` settings once instead of retyping flags. Set
`DRY_RUN=1` to print the `docker`/`podman` command instead of running it
— handy for checking what will be mounted before you commit to it.

### Already have the image, or a container running?

Before running `start_local.sh`, it's worth checking whether you already
have what you need — it avoids a multi-GB re-download and duplicate
containers.

**1. Check which image tag you already have locally:**

```bash
docker images | grep iic-osic-tools
```

`start_local.sh` defaults to tag `latest`. If what you have locally is a
different tag (e.g. companion repos like `SG13G2_ASIC-Design-FLL` pin a
dated tag such as `2026.05` via their own `make docker-start`), pass it
explicitly so the script reuses your local image instead of pulling
`latest` from scratch:

```bash
./start_local.sh --tag 2026.05 --mount "$(pwd)" --mount ../SG13G2_ASIC-Design-FLL
```

**2. Check whether a container is already running:**

```bash
docker ps -a --filter name=iic-osic-tools
```

Companion repos with their own `make docker-install` / `make
docker-start` (e.g. `SG13G2_ASIC-Design-FLL`, see its `CLAUDE.md`) launch
a *different* container — typically named `iic-osic-tools_xvnc_uid_<uid>`
— using their own VNC-capable launcher script, not `start_local.sh`.
That's a separate container from the `iic-osic-tools_shell_uid_<uid>`
one `start_local.sh` creates; both can coexist.

That existing container often already bind-mounts the *parent* directory
of the repo that started it to `/foss/designs` — which means any sibling
repo (this one included, if they share a parent folder) is likely
**already visible inside it** without running `start_local.sh` at all.
Check its mounts:

```bash
docker inspect iic-osic-tools_xvnc_uid_<uid> \
    --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

If the repo(s) you need already show up under `/foss/designs/...` there,
skip `start_local.sh` and just attach to that container directly:

```bash
docker exec -it iic-osic-tools_xvnc_uid_<uid> bash
```

Only reach for `start_local.sh` when you want a separate shell-only
container, or want explicit control over exactly what's mounted.

### Running commands inside the container (`scripts/docker_run.sh`)

Once a container is running, the `make aion-*` targets don't talk to it
directly — they go through `scripts/docker_run.sh` (a second copy lives at
`tools/aion_layout/scripts/docker_run.sh` for that tool's own targets),
which runs a single command inside the container non-interactively via
`docker exec` and returns.

**Find the exact container name** it needs to target:

```bash
docker ps -a --filter name=iic-osic-tools --format '{{.Names}} {{.Status}}'
```

Each `docker_run.sh` defaults to one specific name built from your host
user ID (`$(id -u)`), matching whichever launcher normally starts that
container:

| Script | Default target | Matches |
|--------|-----------------|---------|
| `scripts/docker_run.sh` (repo root) | `iic-osic-tools_shell_uid_<your uid>` | the container `./start_local.sh` creates |
| `tools/aion_layout/scripts/docker_run.sh` | `iic-osic-tools_xvnc_uid_<your uid>` | the container a companion repo's own `make docker-start` creates (see [Already have the image, or a container running?](#already-have-the-image-or-a-container-running)) |

If the name `docker ps` shows doesn't match the default for the script
you're using — e.g. you're running `aion_layout` targets but only have a
`..._shell_...` container up, or vice versa — point it at the right one
with `CONTAINER_NAME`:

```bash
CONTAINER_NAME=iic-osic-tools_shell_uid_1001 ./scripts/docker_run.sh "echo hello from the container"
```

That example runs `echo hello from the container` inside the container
and streams its output back to your terminal; any `make aion-*` target
that shells out through `docker_run.sh` picks up the same `CONTAINER_NAME`
override if you export it first (`export CONTAINER_NAME=...`).

## Available targets

| Target | Description |
|--------|-------------|
| `make aion-opt-run-all` | Full aion_opt flow end-to-end |
| `make aion-opt-graph2verilog` | Convert netlist to structural Verilog |
| `make aion-opt-generate-cells` | Mine patterns and emit AION cells |
| `make aion-opt-rewrite` | Rewrite netlist using generated cells |
| `make aion-opt-lec` | Logical equivalence check |
| `make aion-opt-sec` | Sequential equivalence check |
| `make aion-opt-clean` | Remove aion_opt build outputs |
| `make aion-char-generate` | Generate SV/SPICE testbenches for AION cells |
| `make aion-char-sv` | Run SystemVerilog testbenches |
| `make aion-char-spice` | Run SPICE testbenches |
| `make aion-char-all` | Run SV + SPICE testbenches |
| `make aion-char-lib` | Characterize a cell into Liberty `.lib` files |
| `make aion-char-verify-spice` | Verify a custom SPICE netlist for a cell |
| `make aion-char-clean` | Remove aion_char build outputs |
| `make aion-minimizer-run` | Minimize a gate-level SPICE netlist |
| `make aion-minimizer-verify-spice CELL=...` | Minimize and verify with aion_char SPICE |
| `make aion-minimizer-clean` | Remove aion_minimizer build outputs |
| `make clean` | Remove all build outputs |

## Flow overview

AION Flow is split into three tools. Each has its own directory, Makefile targets, and README with full usage details.

### Cluster extraction — `aion_opt`

The `aion_opt` tool (under `tools/aion_opt/`) takes a post-synthesis netlist, mines recurring combinational patterns, generates new structural Verilog cells, and rewrites the netlist to use them.

See [`tools/aion_opt/README.md`](tools/aion_opt/README.md) for commands, configuration flags, and YAML config.

### Cell validation and characterization — `aion_char`

The `aion_char` tool (under `tools/aion_char/`) validates the AION cells produced by `aion_opt` with exhaustive testbenches and characterizes them into Liberty libraries.

See [`tools/aion_char/README.md`](tools/aion_char/README.md) for commands and configuration flags.

### Gate-level SPICE minimization — `aion_minimizer`

The `aion_minimizer` tool (under `tools/aion_minimizer/`) takes a small gate-level SPICE netlist and merges the gate instances into a single optimized transistor-level SPICE netlist. It can also feed the result into `aion_char` for SPICE verification.

See [`tools/aion_minimizer/README.md`](tools/aion_minimizer/README.md) for commands and configuration flags.
