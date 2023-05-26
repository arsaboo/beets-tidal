# beets-tidal
A plugin for [beets](https://github.com/beetbox/beets) to use JioSaavn as a metadata source.

## Installation

Install the plugin using `pip`:

```shell
pip install git+https://github.com/arsaboo/beets-tidal.git
```

Then, [configure](#configuration) the plugin in your
[`config.yaml`](https://beets.readthedocs.io/en/latest/plugins/index.html) file.

## Configuration

Add `Tidal` to your list of enabled plugins.

```yaml
plugins: tidal
```

## Features

The following features are implemented in `tidal`:

* `beet tidalsync [-f]`: obtain popularity information for every track in the library. By default, `tidalsync` will skip tracks that already have this information populated. Using the `-f` or `--force` option will download the data even for tracks that already have it. Please note that `tidalysync` works only on tracks that have the Tidal track identifiers. So run tidalsync only after importing your music with Tidal, during which these  identifiers will be added for tracks where Tidal is chosen as the tag source.