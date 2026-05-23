# Commons API Reference

Common API endpoints for interacting with Wikimedia Commons.

## Action API

Base: `https://commons.wikimedia.org/w/api.php`

### Search files
```
action=query&list=search&srsearch=query&srnamespace=6&format=json
```
Namespace 6 is the `File:` namespace — limits results to media files.

### Get file metadata
```
action=query&prop=imageinfo&iiprop=url|user|extmetadata|size|mime&titles=File:Penguins_Logo.svg&format=json
```

### Get file usage across wikis
```
action=query&prop=globalusage&titles=File:Penguins_Logo.svg&format=json
```

### Get file categories
```
action=query&prop=categories&titles=File:Penguins_Logo.svg&format=json
```

## REST API

Base: `https://commons.wikimedia.org/api/rest_v1/`

### File metadata
```
GET /page/file/{title}/metadata
```

### Image thumbnail (scaled to width)
```
GET /page/image/{title}/{width}px
```

### File download
```
GET /page/pdf/{title}  (for PDF files)
```

## MediaSearch API

MediaSearch is a dedicated search backend. Access it via the Action API:

```
action=query&list=search&srsearch=query&srnamespace=6&srbackend=MediaSearch&format=json
```

The `srbackend=MediaSearch` parameter selects the newer MediaSearch backend instead of CirrusSearch. Available in MediaWiki 1.37+.

## License Detection

File metadata via `iiprop=extmetadata` returns a `LicenseShortName` or `LicenseUrl` field that indicates the file's license. Common values:

| LicenseShortName | LicenseUrl |
|-----------------|-----------|
| `CC0` | `https://creativecommons.org/publicdomain/zero/1.0/` |
| `CC BY-SA 4.0` | `https://creativecommons.org/licenses/by-sa/4.0/` |
| `CC BY 4.0` | `https://creativecommons.org/licenses/by/4.0/` |
| `Public Domain` | Varies (PD-old, PD-US, etc.) |
