#/bin/bash

pgrep Google Chrome | xargs kill -9
pgrep Chromedriver | xargs kill -9