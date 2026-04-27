docker run --rm -it `
  --network host `
  -v "${PWD}:/workspace" `
  -w /workspace `
  duckdb/duckdb /duckdb -init setup.sql -ui
