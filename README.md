# claude-plugins

A Claude Code plugin marketplace and, in the same repository, the Python package
`claude-plugins-tools` (console script `cpt`) that the plugins' skills and hooks rely on.

Each directory under `plugins/` is one plugin, listed in `.claude-plugin/marketplace.json`.
The marketplace carries no `version`: the commit SHA is the version, so each push is an update.

## Declaring it in a project

In the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-plugins": {
      "source": { "source": "github", "repo": "aneuraz/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "core@claude-plugins": true
  }
}
```

Add one `rules-<pack>@claude-plugins` entry per rule pack the project wants.

## Auto-update

Auto-update is off by default for a third-party marketplace. Each user turns it on once:
run `/plugin`, open the Marketplaces tab, select `claude-plugins` and enable auto-update.

## Development

```
uv sync
uv run pytest
uv run ruff check
uv run ruff format --check
claude plugin validate plugins/core
```

Licensed under the MIT licence.
