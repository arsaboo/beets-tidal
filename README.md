# beets-tidal

A plugin for [beets](https://github.com/beetbox/beets) to use Tidal as a metadata source for music tagging and enrichment.

## Requirements

- **Python**: 3.8 or higher
- **beets**: 1.6.0 or higher
- **tidalapi**: For Tidal API interactions
- **requests**: HTTP library
- **pillow**: Image processing library

## Installation

### Install from GitHub

```shell
pip install git+https://github.com/arsaboo/beets-tidal.git
```

Alternatively, clone the repository and install locally:

```shell
git clone https://github.com/arsaboo/beets-tidal.git
cd beets-tidal
pip install -e .
```

### Configuration

Add `tidal` to your list of enabled plugins in your beets configuration file (`~/.config/beets/config.yaml` on Linux/macOS or `%APPDATA%\beets\config.yaml` on Windows):

```yaml
plugins:
  - tidal

tidal:
  data_source_mismatch_penalty: 0.5
  tidal_attempts: 5
  tidal_sleep_interval: [5, 30]
  tidal_session_file: tidal.json
```

#### Configuration Options

- **data_source_mismatch_penalty** (default: 0.5): Penalty applied when the metadata source doesn't match Tidal during autotagging. Lower values increase Tidal's priority.
- **source_weight** (deprecated): Legacy option for backward compatibility. Use `data_source_mismatch_penalty` instead. Will be removed in v3.0.0.
- **tidal_attempts** (default: 5): Number of attempts to make when fetching data from Tidal API.
- **tidal_sleep_interval** (default: [5, 30]): Sleep interval (in seconds) between API calls. Provide as a range `[min, max]`.
- **tidal_session_file** (default: tidal.json): Location where Tidal OAuth session is saved.

### First Run - Authentication

When you run beets with the Tidal plugin enabled for the first time, you'll be prompted to authenticate with Tidal using OAuth. Follow the on-screen instructions to complete the login process. Your session credentials will be saved for future use.

## Features

The plugin provides the following features:

### Metadata Source for Autotagger

Use Tidal as a metadata source when importing music with beets:

```shell
beet import /path/to/music
```

During import, you can select Tidal as the source for track and album metadata, including:
- Album and artist names
- Track information (title, length, ISRC)
- Popularity scores
- Album artwork

### tidalsync Command

Fetch or update track popularity information from Tidal for your library:

```shell
beet tidalsync
```

#### tidalsync Options

- **Default behavior**: Skips tracks that already have popularity information. Use this for a quick update of new tracks.
- **`-f, --force`**: Re-downloads popularity data even for tracks that already have it. Use this to refresh all popularity scores.

**Note**: The `tidalsync` command only works on tracks that have Tidal track identifiers. These are automatically added during import when Tidal is selected as the metadata source.

### Item Attributes

When importing from Tidal, the following attributes are added to items:

- `tidal_track_id`: Tidal track identifier
- `tidal_album_id`: Tidal album identifier
- `tidal_artist_id`: Tidal artist identifier
- `tidal_track_popularity`: Track popularity score (0-100)
- `tidal_alb_popularity`: Album popularity score
- `tidal_updated`: Timestamp of last update

## Usage Examples

### Import music with Tidal

```shell
beet import --search ~/Downloads/music
```

When prompted to choose a source, select Tidal for albums/tracks you want to tag with Tidal metadata.

### Update popularity for all tracks

```shell
beet tidalsync
```

### Force refresh popularity data

```shell
beet tidalsync --force
```

### Query by popularity

```shell
beet list tidal_track_popularity:'>80'  # List tracks with popularity > 80
```

## Troubleshooting

### "Could not import plugin tidal" error

This typically indicates an import issue or missing dependency. Ensure:
1. All required packages are installed: `pip install beets tidalapi requests pillow`
2. Your beets version is 1.6.0 or higher: `beet version`

### Authentication issues

If you encounter authentication problems:
1. Delete the session file specified in `tidal_session_file` config
2. Restart beets to trigger re-authentication

### No tracks found during search

Ensure you're searching for music that exists on Tidal. Try searching for popular artists or albums first.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests on [GitHub](https://github.com/arsaboo/beets-tidal).

## License

This plugin is released under the MIT License. See the [LICENSE](LICENSE) file for details.
