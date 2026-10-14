#!/bin/bash
set -e

event_info=$(cat)

session_id=$(echo "$event_info" | jq -r '.session_id // empty')

cache_dir="$CLAUDE_PROJECT_DIR/.claude/tsc-cache/${session_id:-default}"

if [[ ! -d "$cache_dir" ]]; then
    exit 0
fi

if [[ ! -f "$cache_dir/affected-repos.txt" ]]; then
    exit 0
fi

results_dir="$cache_dir/results"
mkdir -p "$results_dir"

total_errors=0
has_errors=false

count_tsc_errors() {
    local output="$1"
    echo "$output" | grep -E "\.tsx?.*:.*error TS[0-9]+:" | wc -l | tr -d ' '
}

> "$results_dir/error-summary.txt"

while IFS= read -r repo; do
    tsc_cmd=$(grep "^$repo:tsc:" "$cache_dir/commands.txt" 2>/dev/null | cut -d':' -f3-)

    if [[ -z "$tsc_cmd" ]]; then
        continue
    fi

    if ! output=$(eval "$tsc_cmd" 2>&1); then
        has_errors=true

        error_count=$(count_tsc_errors "$output")
        total_errors=$((total_errors + error_count))

        echo "$output" > "$results_dir/$repo-errors.txt"
        echo "$repo:$error_count" >> "$results_dir/error-summary.txt"
    else
        echo "$repo:0" >> "$results_dir/error-summary.txt"
    fi
done < "$cache_dir/affected-repos.txt"

if [[ "$has_errors" == "true" ]]; then
    > "$cache_dir/last-errors.txt"
    for error_file in "$results_dir"/*-errors.txt; do
        if [[ -f "$error_file" ]]; then
            repo_name=$(basename "$error_file" -errors.txt)
            echo "=== Errors in $repo_name ===" >> "$cache_dir/last-errors.txt"
            cat "$error_file" >> "$cache_dir/last-errors.txt"
            echo "" >> "$cache_dir/last-errors.txt"
        fi
    done

    cp "$cache_dir/commands.txt" "$cache_dir/tsc-commands.txt"

    if [[ $total_errors -ge 5 ]]; then
        echo "" >&2
        echo "## TypeScript Build Errors Detected" >&2
        echo "" >&2
        echo "Found $total_errors TypeScript errors across the following repos:" >&2
        while IFS=':' read -r repo count; do
            if [[ $count -gt 0 ]]; then
                echo "- $repo: $count errors" >&2
            fi
        done < "$results_dir/error-summary.txt"
        echo "" >&2
        echo "Please use the auto-error-resolver agent to fix these errors systematically." >&2
        echo "The error details have been cached for the resolver to use." >&2
        echo "" >&2
        echo "Run: Task(subagent_type='auto-error-resolver', description='Fix TypeScript errors', prompt='Fix the TypeScript compilation errors found in the cached error log')" >&2

        # Exit with status 2 to send feedback to Claude
        exit 2
    else
        echo "" >&2
        echo "## Minor TypeScript Errors" >&2
        echo "" >&2
        echo "Found $total_errors TypeScript error(s). Here are the details:" >&2
        echo "" >&2

        cat "$cache_dir/last-errors.txt" | sed 's/^/  /' >&2
        echo "" >&2
        echo "Please fix these errors directly in the affected files." >&2

        # Exit with status 2 to send feedback to Claude for any errors
        exit 2
    fi
else
    rm -rf "$cache_dir"

    exit 0
fi
