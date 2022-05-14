#!/bin/bash

# print python version
python3 -V

# clone required repos
git clone --depth 1 https://gitlab.com/kicad/libraries/kicad-footprints.git $CI_BUILDS_DIR/kicad-footprints


SCRIPT="$CI_BUILDS_DIR/kicad-library-utils/klc-check/check_package3d.py"

# extract the bash SHA hash from the gitlab API
# unfortunately it is not available via the environment variables
API_RESPONSE=$(curl -s -H "JOB_TOKEN: $CI_JOB_TOKEN" "https://gitlab.com/api/v4/projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID")
BASE_SHA=$( echo $API_RESPONSE | python3 -c "import sys, json; print (json.load(sys.stdin)['diff_refs']['base_sha'])")
TARGET_SHA=$( echo $API_RESPONSE | python3 -c "import sys, json; print (json.load(sys.stdin)['diff_refs']['head_sha'])")

PCKG_FILE_ERROR_CNT=0

echo "Comparing range $BASE_SHA to $TARGET_SHA"
for change in $(git diff-tree --diff-filter=AMR --no-commit-id --name-only -r "$BASE_SHA" "$TARGET_SHA"); do
    if [[ $change =~ .*\.step || $change =~ .*\.wrl ]]; then
        echo "Checking: $change"
        python3 "$SCRIPT" "/$CI_PROJECT_DIR/$change" -vv
        PCKG_FILE_ERROR_CNT="$(($PCKG_FILE_ERROR_CNT + $?))"
	else
		echo "Both *.step and *.wrl files required."
    fi
done
echo "ErrorCount $PCKG_FILE_ERROR_CNT" > metrics.txt