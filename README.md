# PDF Factory

PDF Factory is a Python library that helps you assemble PDFs and HTML and to produce a single PDF.

As always, comments and contributions welcome ! :)

## Features :

 - Take a JSON (local or remote) configuration and generate a PDF.
 - If item `uri` is a web-page, convert it using [WKHTMLTOPDF](https://github.com/antialize/wkhtmltopdf).
 - Can fill PDF forms with given `data` attributes.
 - Can store each PDF or the whole file for caching (see `output` and `overwrite`).
 - Can send a GET request to the specified `callback` to notify the system of the result.

## Usage example:

```bash
./pdfFactory.py devis.json
./pdfFactory.py http://foo.bar/devis.json
```

sample json configuration:

```js
{
    /* where to store the resulting file */
    "output": "report/MyAwesomeSalesQuote.pdf",
    /* overwrite:
    	- true: always regenerate a new PDF (default)
    	- false: use the local output file if already exists
    */
    "overwrite": true,
    /* URL to call when generation complete (optional) */
    "callback": "http://foo.bar/devis?done=4564&key=XXXXXX",
    /*  if you want to fill any PDF with some data (optional) 
    	this will fill the PDF fields accordingly
    */
    "data": { 
    	"date": "21.03.2412",
    	"ref": "XX-WYZ"
    },
    /* content of the final PDF */
    "items": [{
    	/* can be a local/remote PDF or any URL */
        "uri": "/srv/devis/frontpage.pdf",
        /*  if you want to fill this PDF with some data (optional) 
	    	this will fill the PDF fields accordingly
	    	this data will override the global data object
	    */
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
        /* options for WKHTMLTOPDF */
        "options": ["--window-status", "ready", '--margin', 10],
        /* if you want this section to be saved on disk after processing (optionnal) */
        "output": "/srv/cache/pink_handcuffs.pdf"
    }, {
        "uri": "http://foo.bar/tos"
    }]
}
```

## Todo :

- Recursive call if JSON

## Licence
This script is released under the permissive [MIT license](http://revolunet.mit-license.org). Your contributions are always welcome.
