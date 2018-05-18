Flask app wrapping [scrapy-cr.justice.gov.lb](https://github.com/shadiakiki1986/scrapy-cr.justice.gov.lb) via [scrapyrt](http://scrapyrt.readthedocs.io/)


## Usage

Set `GOOGLE_APPLICATION_KEY` in `docker-compose.yml` to get arabic-english translation of names

## Changelog

0.1 (2018-05-17)
- can either type in register number/place or upload xlsx file (examples in-page)


## Dev notes

```
docker-compose build
git submodule init
```

## Dev notes 2
```
cd scrapy-cr.justice.gov.lb
scrapyrt -i 0.0.0.0 -p 3006

cd ...
FLASK_ENV=development SCRAPYRT=http://0.0.0.0:3006 FLASK_APP=app.py flask run -h 0.0.0.0 -p 3000
```
