#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
bash $SCRIPT_DIR/.staging_workflows/normalize.sh dev
cd ..
act -P ubuntu-latest=drewyangdev/ubuntu:act-latest \
    --secret-file $SCRIPT_DIR/.test/.secrets \
    --artifact-server-path $SCRIPT_DIR/.test/artifacts/