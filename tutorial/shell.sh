#!/bin/bash
docker run --rm -it \
  --network host \
  -v "$(pwd):/workspace" \
  -w /workspace \
  duckdb/duckdb /duckdb -init setup.sql -ui
