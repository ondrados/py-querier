#!/bin/sh

find . -type f -name "test_*.db" -delete
pytest --disable-warnings
