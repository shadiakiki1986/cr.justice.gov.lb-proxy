Flask app wrapping [scrapy-cr.justice.gov.lb](https://github.com/shadiakiki1986/scrapy-cr.justice.gov.lb) via [scrapyrt](http://scrapyrt.readthedocs.io/)


## Usage

For defaults, just `docker-compose up -d` (regular docker-fu)

To get arabic-english translation of names
- Copy `docker-compose.override.yml.dist` to `docker-compose.override.yml`
- Set `GOOGLE_APPLICATION_KEY` in `docker-compose.override.yml`


## Changelog

0.1 (2018-05-17)
- can either type in register number/place or upload xlsx file (examples in-page)


## Dev notes

```
# first git checkout
git submodule init

# or for later submodule updates
git submodule foreach git pull origin master

# build
docker-compose build
```

## Dev notes 2
```
cd scrapy-cr.justice.gov.lb
scrapyrt -i 0.0.0.0 -p 3006

cd ...
FLASK_ENV=development SCRAPYRT=http://0.0.0.0:3006 FLASK_APP=app.py flask run -h 0.0.0.0 -p 3000
```
