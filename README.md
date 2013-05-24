# PDF Factory

PDF Factory is a Python script/module that parse a JSON to generate a PDF from several webpages or other PDF.

As always, comments and contributions welcome ! :)

## Usage example:

./pdfFactory devis.json
./pdfFactory http://foo.bar/devis.json

with json:

```json
{
  "output": "report/MyAwesomeSalesQuote.pdf",
	"callback": "http://foo.bar/devis?done=4564&key=XXXXXX",
	"data": { "date": "21.03.2412" },
	"items": [{
		"uri": "/srv/devis/frontpage.pdf",
		"data":
			{
				"ADRESSE2": "23 Boulevard de Clichy",
				"CP": "75009",
				"VILLE": "Paris",
				"TELDOM": "+33102030405",
				"EMAIL": "laurent@revolunet.com",
				"PRENOM": "Laurent",
				"NOM": "Mox"
			}
	}, {
		"uri": "http://foo.bar/product?id=54654",
		"options": ["--window-status", "ready"],
		"output": "/srv/cache/pink_handcuffs.pdf",
		"overwrite": false
	}, {
		"uri": "http://foo.bar/tos"
	}]
}
```

## Features :

 - Take a JSON (local or remote) as configuration and generate a PDF.
 - If item URI is a web-page, convert it using [WKHTMLTOPDF](https://github.com/antialize/wkhtmltopdf).
 - Can add data to PDF if it contain inputs.
 - Can store each piece of PDF or the whole file for caching.
 - Can send a GET request to a specified callback to notify the system.

## Todo :

- Recursive call if JSON

## Licence
This script is released under the permissive [MIT license](http://revolunet.mit-license.org). Your contributions are always welcome.