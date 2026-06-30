# beets-tidal — **DEPRECATED**

> **This repository is no longer maintained.** All features have been merged into the official [beets Tidal plugin](https://beets.readthedocs.io/en/stable/plugins/tidal.html). Please use that instead.

## Migration

1. **Remove** this plugin:
   ```shell
   pip uninstall beets-tidal
   ```

2. **Install** the official plugin:
   ```shell
   pip install "beets[tidal]"
   ```

3. **Authenticate**:
   ```shell
   beet tidal --auth
   ```

The official plugin supports everything this one did — `beet tidalsync`, flexible attributes (`tidal_track_id`, `tidal_track_popularity`, etc.), cover art, and more — with a cleaner codebase and ongoing maintenance.

For full documentation, see: https://beets.readthedocs.io/en/stable/plugins/tidal.html
