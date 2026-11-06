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
    "aneuraz-plugins": {
      "source": { "source": "github", "repo": "aneuraz/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "core@aneuraz-plugins": true
  }
}
```

Add one `rules-<pack>@aneuraz-plugins` entry per rule pack the project wants.

## Auto-update

Auto-update is off by default for a third-party marketplace. Each user turns it on once:
run `/plugin`, open the Marketplaces tab, select `aneuraz-plugins` and enable auto-update.

## Development

```
uv sync
uv run pytest
uv run ruff check
uv run ruff format --check
claude plugin validate plugins/core
```

The `core` plugin has two evals, `finds-a-pack-rule` and `finds-a-pack-rule-in-other-words`; their command and prerequisites are in the header of `plugins/core/evals/finds-a-pack-rule/case.yaml`.

Licensed under the MIT licence.
