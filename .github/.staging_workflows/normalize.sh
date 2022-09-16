#!/bin/bash
# For Github Action that doesn't support anchor yet...
# https://github.com/actions/runner/issues/1182

STAGE=$1
# .yaml in .staging_workflows has to be named using a prefix 'anchored_', this will be removed when normalizing
PREFIX="anchored_" 
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
for source in $(ls $SCRIPT_DIR | grep yaml)
do
    target=${source#$PREFIX}
    export STAGE
    envsubst '${STAGE}' < $SCRIPT_DIR/$source | yq e 'explode(.) | del(.anchor-*)' > $SCRIPT_DIR/../workflows/$target
done