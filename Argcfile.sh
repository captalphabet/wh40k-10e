#!/usr/bin/env bash

set -e

# @cmd run cli tool
# @arg file! file to read
runcli() {
  cargo run --manifest-path "./utils/xml-parsing/Cargo.toml" -- --file "$argc_file"
}




# See more details at https://github.com/sigoden/argc
eval "$(argc --argc-eval "$0" "$@")"
