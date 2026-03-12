# 🎨 cli-anything-figma

**Figma CLI for AI Agents** — Make Figma agent-ready with one install.

Built following the [CLI-Anything](https://github.com/HKUDS/CLI-Anything) methodology. Every command returns structured JSON for agents, rich tables for humans, and the whole thing works as an interactive REPL or one-shot subcommands.

---

## ✨ What It Does

Wraps the **entire Figma REST API** into a single CLI that any AI agent (Claude Code, Cursor, Windsurf, OpenCode, Codex, etc.) can call directly:

- **Files** — Inspect structure, list pages, walk the node tree
- **Export** — Render any node to PNG/SVG/PDF/JPG, download to disk
- **Components** — Browse file & team library components
- **Styles** — List and inspect published styles
- **Comments** — Read, post, reply, delete comments
- **Projects** — Browse team projects and their files
- **Variables** — List variables and variable collections
- **Versions** — File version history
- **Webhooks** — Manage team webhooks
- **Config** — Store your token once, use everywhere

Every command supports `--json` for machine output, `--help` for self-discovery, and works in both one-shot and interactive REPL modes.

---

## 🚀 Installation (3 Steps)

### Prerequisites

- **Python 3.10+**
- A **Figma Personal Access Token** — [Generate one here](https://www.figma.com/developers/api#access-tokens)

### Step 1: Clone & Install

```bash
git clone https://github.com/superdwayne/figma-cli.git
cd figma-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

After this, `figma-cli` and `cli-anything-figma` are both on your PATH.

### Step 2: Set Your Figma Token

**Option A — CLI config (persisted to disk):**
```bash
figma-cli config set-token figd_YOUR_TOKEN_HERE
```

**Option B — Environment variable (per session):**
```bash
export FIGMA_ACCESS_TOKEN=figd_YOUR_TOKEN_HERE
```

**Option C — Add to your shell profile (permanent):**
```bash
echo 'export FIGMA_ACCESS_TOKEN=figd_YOUR_TOKEN_HERE' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Verify It Works

```bash
figma-cli config check
# ✓ Authenticated as yourname (you@email.com)
```

Optionally set a default team ID:
```bash
figma-cli config set-team 123456789
```

---

## 🤖 Using With AI Agents

### Claude Code

Once installed, Claude Code can call `figma-cli` directly via shell commands:

```
# Ask Claude Code to inspect a Figma file
> Use figma-cli to get the structure of file abc123XYZ

# Claude runs:
figma-cli --json file --file abc123XYZ info
figma-cli --json file --file abc123XYZ list-pages
figma-cli --json file --file abc123XYZ tree --depth 3
```

### Cursor / Windsurf / Any Agent

Any agent that can run terminal commands can use the CLI. The `--json` flag ensures structured output that agents can parse directly:

```bash
# Agent discovers available commands
figma-cli --help

# Agent gets file info as JSON
figma-cli --json file --file <FILE_KEY> info

# Agent exports a frame as PNG
figma-cli export --file <FILE_KEY> render --ids "1:0" --format png -o ./exports

# Agent lists all components
figma-cli --json component list --file <FILE_KEY>

# Agent reads design tokens (variables)
figma-cli --json variable --file <FILE_KEY> list
```

### How Agents Discover Commands

```bash
# List all command groups
figma-cli --help

# List subcommands in a group
figma-cli file --help
figma-cli export --help
figma-cli component --help

# Get detailed help for a specific command
figma-cli file info --help
figma-cli export render --help
```

### Agent Workflow Example

Here's a typical design-to-code workflow an agent can run:

```bash
# 1. Get file overview
figma-cli --json file --file abc123 info

# 2. List all pages
figma-cli --json file --file abc123 list-pages

# 3. Walk the node tree to find target frames
figma-cli --json file --file abc123 tree --depth 4 --page "Components"

# 4. Export specific nodes as images
figma-cli export --file abc123 render --ids "2:45,2:67" --format png -o ./design-refs

# 5. Get component details
figma-cli --json component list --file abc123

# 6. Get design tokens / variables
figma-cli --json variable --file abc123 list

# 7. Get published styles (colors, text styles)
figma-cli --json style list --file abc123
```

---

## 🎮 Usage

### One-Shot Subcommands (for scripts & agents)

```bash
# File operations
figma-cli file --file <KEY> info
figma-cli file --file <KEY> list-pages
figma-cli file --file <KEY> tree --depth 3
figma-cli file --file <KEY> nodes --ids "1:0,2:1"

# Export
figma-cli export --file <KEY> render --ids "1:0,2:1" -F png -o ./exports
figma-cli export --file <KEY> urls --ids "1:0" -F svg
figma-cli export --file <KEY> fills

# Components
figma-cli component list --file <KEY>
figma-cli component list-sets --file <KEY>
figma-cli component get --key <COMPONENT_KEY>
figma-cli component team-list --team <TEAM_ID>

# Styles
figma-cli style list --file <KEY>
figma-cli style get --key <STYLE_KEY>
figma-cli style team-list --team <TEAM_ID>

# Comments
figma-cli comment --file <KEY> list
figma-cli comment --file <KEY> post -m "Looks great!"
figma-cli comment --file <KEY> reply -c <COMMENT_ID> -m "Thanks!"
figma-cli comment --file <KEY> delete -c <COMMENT_ID>

# Projects
figma-cli project list --team <TEAM_ID>
figma-cli project files --project-id <PROJECT_ID>

# Versions
figma-cli version --file <KEY> list

# Variables
figma-cli variable --file <KEY> list
figma-cli variable --file <KEY> list --published
figma-cli variable --file <KEY> collections

# Webhooks
figma-cli webhook list --team <TEAM_ID>
figma-cli webhook create --team <TEAM_ID> -e FILE_UPDATE -u https://hook.example.com -p secret123
figma-cli webhook delete --webhook-id <ID>

# User / Config
figma-cli me
figma-cli config show
figma-cli config check
```

### JSON Mode (Agent-Optimized)

Prepend `--json` to get structured output from any command:

```bash
figma-cli --json file --file abc123 info
```
```json
{
  "name": "Design System v3",
  "last_modified": "2025-03-10T14:30:00Z",
  "version": "987654321",
  "role": "editor",
  "pages": 5,
  "page_names": ["Cover", "Components", "Tokens", "Icons", "Playground"]
}
```

```bash
figma-cli --json component list --file abc123
```
```json
[
  {
    "key": "abc123def",
    "name": "Button",
    "description": "Primary action button with variants",
    "containing_frame": "Components"
  }
]
```

```bash
figma-cli --json variable --file abc123 list
```
```json
{
  "variables": [
    {
      "id": "var1",
      "name": "primary-color",
      "resolved_type": "COLOR",
      "collection": "Design Tokens",
      "description": "Primary brand color"
    }
  ],
  "collections": [
    {
      "name": "Design Tokens",
      "modes": [{"name": "Light"}, {"name": "Dark"}],
      "variableIds": ["var1", "var2"]
    }
  ]
}
```

### REPL Mode (Interactive Sessions)

Run `figma-cli` with no arguments to enter the interactive shell:

```
$ figma-cli
╔══════════════════════════════════════════════╗
║  cli-anything-figma  v1.0.0                 ║
║  Figma CLI for AI Agents                    ║
╚══════════════════════════════════════════════╝

figma> me
┌──────────────┬──────────────────┐
│ Handle       │ alice            │
│ Email        │ alice@company.co │
│ ID           │ 12345            │
└──────────────┴──────────────────┘

figma> file --file abc123xyz info
✓ File: Design System v3 (5 pages, editor)

figma> component list --file abc123xyz
┌─────────┬──────────┬─────────────────┬────────────┐
│ Key     │ Name     │ Description     │ Frame      │
├─────────┼──────────┼─────────────────┼────────────┤
│ comp1   │ Button   │ Primary action  │ Components │
│ comp2   │ Card     │ Card layout     │ Components │
└─────────┴──────────┴─────────────────┴────────────┘

figma> exit
Goodbye! 👋
```

---

## � Finding Your File Key & Team ID

**File Key** — the string in your Figma URL between `/design/` and the file name:
```
https://www.figma.com/design/abc123XYZ/My-Design-File
                              ^^^^^^^^^^
                              This is the file key
```

**Team ID** — found in your Figma team URL:
```
https://www.figma.com/files/team/123456789/My-Team
                                ^^^^^^^^^
                                This is the team ID
```

---

## 🎯 Command Reference

| Command Group | Subcommands | Description |
|---|---|---|
| `file` | `info`, `list-pages`, `tree`, `nodes` | File inspection & structure |
| `export` | `render`, `urls`, `fills` | Export nodes as images |
| `component` | `list`, `list-sets`, `get`, `get-set`, `team-list` | Components & component sets |
| `style` | `list`, `get`, `team-list` | Published styles |
| `comment` | `list`, `post`, `reply`, `delete` | Comment management |
| `project` | `list`, `files` | Team projects & files |
| `version` | `list` | Version history |
| `variable` | `list`, `collections` | Variables & collections |
| `webhook` | `list`, `create`, `delete` | Team webhooks |
| `config` | `set-token`, `set-team`, `show`, `check` | Configuration |
| `me` | — | Current user info |

---

## 📂 Project Structure

```
figma-cli/
├── README.md
├── setup.py                           # pip-installable package
├── requirements.txt
├── cli_anything_figma/
│   ├── __init__.py                    # Version: 1.0.0
│   ├── cli.py                         # Click CLI + REPL launcher
│   ├── api.py                         # Figma REST API client
│   ├── config.py                      # Token & config management
│   ├── formatters.py                  # JSON + Rich table output
│   ├── repl_skin.py                   # Interactive REPL shell
│   └── commands/
│       ├── file.py                    # info, list-pages, tree, nodes
│       ├── export.py                  # render, urls, fills
│       ├── component.py               # list, get, team-list
│       ├── style.py                   # list, get, team-list
│       ├── comment.py                 # list, post, reply, delete
│       ├── project.py                 # list, files
│       ├── version.py                 # list
│       ├── variable.py                # list, collections
│       ├── webhook.py                 # list, create, delete
│       └── config_cmd.py             # set-token, set-team, show, check
└── tests/
    ├── conftest.py                    # Shared test fixtures
    ├── test_api.py                    # 15 API unit tests
    └── test_cli.py                    # 23 CLI integration tests
```

---

## �️ Architecture (CLI-Anything Design Principles)

1. **Authentic Figma Integration** — Direct calls to the Figma REST API. No mocks, no shortcuts. Every command hits the real platform.

2. **Dual Interaction Modes** — Subcommand interface for scripting/pipelines + REPL for interactive agent sessions.

3. **Agent-Native Design** — `--json` on every command for structured data. `--help` on every command for self-discovery. Agents find the tool via `which figma-cli`.

4. **Consistent Experience** — Unified REPL skin with branded banner, styled prompts, command history, and Rich formatting.

5. **Zero-Config Install** — `pip install -e .` puts both `figma-cli` and `cli-anything-figma` on PATH.

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

38 tests covering API client + all CLI commands.

---

## 📄 License

MIT
