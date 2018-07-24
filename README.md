Flask app wrapping [scrapy-cr.justice.gov.lb](https://github.com/shadiakiki1986/scrapy-cr.justice.gov.lb) via [scrapyrt](http://scrapyrt.readthedocs.io/)


## Pre-requisites

1. install docker ([ubuntu instructions](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-convenience-script))
2. install docker-compose ([ubuntu instructions](https://docs.docker.com/compose/install/#install-compose))


## Usage

For defaults, just `docker-compose up -d` (regular docker-fu)

For more features, copy `docker-compose.override.yml.dist` to `docker-compose.override.yml`:
- To get arabic-english translation of names, set `GOOGLE_APPLICATION_KEY`
- For using https instead of http, use the `proxy` service (reverse proxy nginx redirecting https to http)


## Changelog

0.4 (2018-07-??)
- change file names in zip of html pages to be names instead of numbers

0.3 (2018-07-06)
- merge business name en/ar into `df_out`
- more user-friendly dropdown for format
- add link to wiki for instructions
- use company name (arabic) for sheet names

0.2 (2018-06-25)
- add "zip" format, which is a zip archive of raw html of each company
- add dataframe of "all output" in a single sheet for format=xlsx
- drop index column from format=xlsx


0.1 (2018-05-17)
- can either type in register number/place or upload xlsx file (examples in-page)


## Dev notes

```
# first git checkout
git submodule init
git submodule update

# docker-compose-fu: build and up
docker-compose build
docker-compose up -d

# or for later submodule updates
git submodule foreach git pull origin master

# restart the scrapyrt to load the updated code (scrapyrt doesn't auto-reload like the `FLASK_ENV=development` feature)
docker-compose restart scrapyrt
```

## Dev notes 2
```
cd scrapy-cr.justice.gov.lb
scrapyrt -i 0.0.0.0 -p 3006

cd ...
FLASK_ENV=development SCRAPYRT=http://0.0.0.0:3006 FLASK_APP=app.py flask run -h 0.0.0.0 -p 3000
```
