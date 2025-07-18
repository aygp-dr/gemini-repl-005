#!/usr/bin/env bash 

echo "This is a project I'm working on. Answer the following questions:"; cat .ai/context-eval.json | jq -r '.context_test.questions[].q' | nl -s '. '
