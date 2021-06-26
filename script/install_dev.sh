#!/bin/sh
git config --local core.hooksPath .git-hooks
pipenv install --dev
