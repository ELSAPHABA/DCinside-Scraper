#!/bin/sh
set -eu

exec python -m dcinside_scraper.adapters.container "$@"
