#!/bin/bash
FILES=../log/tty/*
for f in $FILES
do
  echo "__________________________________"
  echo "Processing $f file..."
  python playlog.py -m 2 -w file $f
done
