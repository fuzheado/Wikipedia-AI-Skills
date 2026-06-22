#!/usr/bin/env bash
# audit-skills.sh — Automated metrics for all skills in .claude/skills/
# Usage: ./scripts/audit-skills.sh [--json]
#   --json   Output as JSON for piping into reports
#   (no flag) Pretty-printed table to stdout

set -euo pipefail
SKILLS_DIR="$(cd "$(dirname "$0")/../.claude/skills" && pwd)"

# --- helpers ---
word_count() { wc -w < "$1" | tr -d ' '; }
line_count() { wc -l < "$1" | tr -d ' '; }
code_blocks() { grep -c '```' "$1" 2>/dev/null || echo 0; }
yaml_field() { awk '/^---$/{if(++c==2) exit; next} c==1' "$1" | { grep "^${2}:" || true; } | sed "s/^${2}: *//" | head -1; }
internal_links() {
    local c1=0 c2=0
    c1=$(grep -c '\[\[.*\]\]' "$1" 2>/dev/null) || c1=0
    c2=$(grep -c '\.\./[a-z][a-z-]*/SKILL\.md' "$1" 2>/dev/null) || c2=0
    echo $((c1 + c2))
}
depends_on_count() { local v; v=$(yaml_field "$1" "depends_on"); if [ -z "$v" ]; then echo 0; else echo "$v" | grep -o '[a-z-]\+' 2>/dev/null | wc -l | tr -d ' '; fi; }
has_field() { awk '/^---$/{if(++c==2) exit; next} c==1' "$1" | { grep -q "^${2}:" && echo "✓" || echo "✗"; } }

# --- collect skill names ---
skills=($(ls -d "$SKILLS_DIR"/*/ 2>/dev/null | while read d; do basename "$d"; done | sort))

JSON=false
[[ "${1:-}" == "--json" ]] && JSON=true

# --- output ---
if $JSON; then
    echo '['
    sep=""
    for name in "${skills[@]}"; do
        file="$SKILLS_DIR/$name/SKILL.md"
        [[ -f "$file" ]] || continue
        desc=$(yaml_field "$file" "description" | sed 's/"/\\"/g')
        echo "${sep}{\"name\":\"${name}\",\"description\":\"${desc}\",\"words\":$(word_count "$file"),\"lines\":$(line_count "$file"),\"internal_refs\":$(internal_links "$file"),\"depends_on_count\":$(depends_on_count "$file"),\"code_blocks\":$(code_blocks "$file")}"
        sep=","
    done
    echo ']'
else
    printf "%-45s %6s %6s %5s %5s %5s %5s\n" "SKILL" "WORDS" "LINES" "REFS" "DEPS" "CODE" "FLAGS"
    printf "%-45s %6s %6s %5s %5s %5s %5s\n" "$(printf '%.0s-' {1..45})" "------" "------" "-----" "-----" "-----" "-----"

    for name in "${skills[@]}"; do
        file="$SKILLS_DIR/$name/SKILL.md"
        [[ -f "$file" ]] || continue
        wc=$(word_count "$file")
        lc=$(line_count "$file")
        ln=$(internal_links "$file")
        dp=$(depends_on_count "$file")
        cb=$(code_blocks "$file")

        # Check required YAML fields
        flags=""
        [[ "$(has_field "$file" "name")" == "✓" ]] || flags+="N"
        [[ "$(has_field "$file" "description")" == "✓" ]] || flags+="D"
        [[ "$(has_field "$file" "license")" == "✓" ]] || flags+="L"
        [[ "$(has_field "$file" "last_verified")" == "✓" ]] || flags+="V"
        [[ -z "$flags" ]] && flags="✓"

        printf "%-45s %6d %6d %5d %5d %5d %5s\n" "$name" "$wc" "$lc" "$ln" "$dp" "$cb" "$flags"
    done

    echo ""
    echo "Flags: N=missing name, D=missing description, L=missing license, V=missing last_verified"
    echo "       ✓ = all fields present"
    echo "Total skills: ${#skills[@]}"
fi
