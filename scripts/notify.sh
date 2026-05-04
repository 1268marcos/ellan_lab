#!/usr/bin/env bash
for p in $(curl /partners | jq -r '.[].email'); do sendmail $p < email/deprecation.txt; done
