#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Remove only the fixed project-generated areas selected by the cleanup level.
set -u

usage() {
    cat <<'USAGE'
Usage: sh tools/project_cleanup.sh --workspace PATH [--tools-root build/NAME] {mostlyclean|clean|distclean}

mostlyclean removes direct build children ending in _stage or _check.
clean removes every direct build child except the configured reusable tools root.
distclean removes the complete build directory. Selected contents, including
unknown files and local history, are removed. Symbolic-link entries are unlinked
without traversing their targets.
USAGE
}

fail() {
    printf 'project cleanup: %s\n' "$*" >&2
    exit 2
}

workspace=
tools_relative_arg=
tools_relative_set=0
level=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --workspace)
            [ "$#" -ge 2 ] || fail '--workspace requires a path'
            workspace=$2
            shift 2
            ;;
        --tools-root)
            [ "$#" -ge 2 ] || fail '--tools-root requires a path'
            tools_relative_arg=$2
            tools_relative_set=1
            shift 2
            ;;
        mostlyclean|clean|distclean)
            [ -z "$level" ] || fail 'select one cleanup level'
            level=$1
            shift
            ;;
        -h|--help) usage; exit 0 ;;
        *) fail "unexpected argument: $1" ;;
    esac
done
[ -n "$workspace" ] || fail '--workspace is required'
[ -n "$level" ] || fail 'a cleanup level is required'
case "$workspace" in /*) ;; *) fail 'workspace path must be absolute' ;; esac
workspace_input=$workspace
[ -d "$workspace" ] || fail "workspace does not exist: $workspace"
[ ! -L "$workspace" ] || fail 'workspace may not be a symbolic link'
workspace_abs=$(CDPATH= cd -P "$workspace" 2>/dev/null && pwd -P) || fail 'cannot resolve workspace'

for utility in awk find wc rm ps lsof; do
    command -v "$utility" >/dev/null 2>&1 || fail "required cleanup utility is unavailable: $utility"
done

if [ "$tools_relative_set" -eq 1 ]; then
    tools_relative=$tools_relative_arg
else
    pyproject=$workspace_abs/pyproject.toml
    [ -f "$pyproject" ] && [ ! -L "$pyproject" ] || fail 'pyproject.toml is missing or is a symbolic link'
    tools_relative=$(awk '
        /^\[tool\.humanmotionlib\.workflow\]$/ { in_workflow=1; next }
        /^\[/ { if (in_workflow) exit }
        in_workflow && /^tools-root[[:space:]]*=/ {
            sub(/^[^=]*=[[:space:]]*"/, "")
            sub(/".*/, "")
            print
            exit
        }
    ' "$pyproject")
fi
[ -n "$tools_relative" ] || fail 'project tools-root setting is missing'
case "$tools_relative" in build/*) tools_name=${tools_relative#build/} ;; *) fail 'tools-root must be a direct child of build/' ;; esac
case "$tools_name" in ''|.|..|*/*|*\\*) fail 'tools-root must be one safe direct-child name' ;; esac
case "$tools_name" in *[!A-Za-z0-9._-]*) fail 'tools-root contains unsupported characters' ;; esac

build=$workspace_abs/build
tools_root=$build/$tools_name
[ ! -L "$build" ] || fail 'build directory may not be a symbolic link'
if [ -d "$build" ]; then
    build_abs=$(CDPATH= cd -P "$build" 2>/dev/null && pwd -P) || fail 'cannot resolve build directory'
    [ "$build_abs" = "$build" ] || fail 'build directory resolves outside the workspace'
elif [ -f "$build" ] || [ -L "$build" ]; then
    fail 'build path is not a directory'
fi
if [ -L "$tools_root" ]; then
    fail 'configured tools-root may not be a symbolic link'
fi
if { [ -f "$tools_root" ] || [ -L "$tools_root" ]; } && [ ! -d "$tools_root" ]; then
    fail 'configured tools-root must be a directory'
fi

exists() {
    [ -f "$1" ] || [ -d "$1" ] || [ -L "$1" ]
}

is_selected_entry() {
    selected_entry=$1
    case "$level" in
        mostlyclean)
            [ "$selected_entry" != "$tools_root" ] || return 1
            case "$selected_entry" in
                "$build"/*_stage|"$build"/*_check|"$build"/.*_stage|"$build"/.*_check) return 0 ;;
                *) return 1 ;;
            esac
            ;;
        clean) [ "$selected_entry" != "$tools_root" ] ;;
        distclean) [ "$selected_entry" = "$build" ] ;;
    esac
}

selected_count=0
if [ -d "$build" ]; then
    if [ "$level" = distclean ]; then
        selected_count=1
    else
        for entry in "$build"/* "$build"/.[!.]* "$build"/..?*; do
            exists "$entry" || continue
            is_selected_entry "$entry" || continue
            selected_count=$((selected_count + 1))
        done
    fi
fi

retained_count=0
if [ "$level" = clean ] && [ -d "$tools_root" ]; then
    retained_count=1
fi
removed_count=0
removed_bytes=0
pending_count=0

if [ "$selected_count" -eq 0 ]; then
    printf 'level=%s\nselected-count=0\nremoved-count=0\nremoved-bytes=0\nretained-count=%s\npending-count=0\n' \
        "$level" "$retained_count"
    if [ "$retained_count" -gt 0 ]; then printf 'retained=%s\n' "$tools_root"; fi
    exit 0
fi

HML_PROJECT_CLEANUP_PID=$$
export HML_PROJECT_CLEANUP_PID
capture_processes() {
    ps -p "$HML_PROJECT_CLEANUP_PID" -o pid= >/dev/null 2>&1 || return 1
    process_snapshot=$(ps -Aww -o pid=,ppid=,stat=,command= 2>/dev/null) || return 1
    printf '%s\n' "$process_snapshot" | awk -v pid="$HML_PROJECT_CLEANUP_PID" '$1 == pid { found=1 } END { exit !found }' || return 2
    lsof_snapshot=$(lsof -nP -Fpcn 2>/dev/null) || return 1
    self_lsof_pid=p$HML_PROJECT_CLEANUP_PID
    printf '%s\n' "$lsof_snapshot" | awk -v pid="$self_lsof_pid" '$0 == pid { found=1 } END { exit !found }' || return 2
    service_pids=" $HML_PROJECT_CLEANUP_PID "
    current_pid=$HML_PROJECT_CLEANUP_PID
    ancestor_steps=0
    while [ "$ancestor_steps" -lt 32 ]; do
        parent_pid=$(printf '%s\n' "$process_snapshot" | awk -v pid="$current_pid" '$1 == pid { print $2; exit }')
        case "$parent_pid" in ''|*[!0-9]*) return 2 ;; esac
        [ "$parent_pid" = 1 ] && break
        case "$service_pids" in *" $parent_pid "*) break ;; esac
        service_pids="$service_pids$parent_pid "
        current_pid=$parent_pid
        ancestor_steps=$((ancestor_steps + 1))
    done
    return 0
}

command_line_uses_area() {
    command_line=$1
    sought_path=$2
    remaining_line=$command_line
    while :; do
        case "$remaining_line" in *"$sought_path"*) ;; *) return 1 ;; esac
        before_path=${remaining_line%%"$sought_path"*}
        after_path=${remaining_line#*"$sought_path"}
        case "$before_path" in
            ''|*' '|*'='|*'"'|*"'"|*':'|*'(') left_boundary=1 ;;
            *) left_boundary=0 ;;
        esac
        case "$after_path" in
            ''|/*|' '*|\"*|\'*|','*|')'*) right_boundary=1 ;;
            *) right_boundary=0 ;;
        esac
        [ "$left_boundary" -eq 1 ] && [ "$right_boundary" -eq 1 ] && return 0
        [ -n "$after_path" ] || return 1
        remaining_line=$after_path
    done
}

process_uses_area() {
    sought_area=$1
    while IFS= read -r process_line || [ -n "$process_line" ]; do
        process_pid=$(printf '%s\n' "$process_line" | awk 'NR == 1 { print $1 }')
        [ -n "$process_pid" ] || return 2
        case "$service_pids" in *" $process_pid "*) continue ;; esac
        process_state=$(printf '%s\n' "$process_line" | awk 'NR == 1 { print $3 }')
        case "$process_state" in Z*) continue ;; esac
        command_line_uses_area "$process_line" "$sought_area" && return 0
    done <<EOF_PS
$process_snapshot
EOF_PS
    current_process=
    while IFS= read -r lsof_line || [ -n "$lsof_line" ]; do
        case "$lsof_line" in
            p*)
                current_process=${lsof_line#p}
                case "$current_process" in ''|*[!0-9]*) return 2 ;; esac
                continue
                ;;
            n*)
                [ -n "$current_process" ] || return 2
                case "$service_pids" in *" $current_process "*) continue ;; esac
                open_path=${lsof_line#n}
                case "$open_path" in "$sought_area"|"$sought_area"/*) return 0 ;; esac
                ;;
        esac
    done <<EOF_LSOF
$lsof_snapshot
EOF_LSOF
    return 1
}

check_area_activity() {
    area=$1
    process_uses_area "$area"
    process_status=$?
    if [ "$process_status" -eq 1 ]; then
        case "$area" in
            "$workspace_abs"/*) alias_area=${workspace_input%/}/${area#"$workspace_abs"/} ;;
            *) alias_area=$area ;;
        esac
        if [ "$alias_area" != "$area" ]; then
            process_uses_area "$alias_area"
            process_status=$?
        fi
    fi
    case "$process_status" in
        0) printf 'active process references %s\n' "$area" >&2; return 1 ;;
        1) return 0 ;;
        *) printf 'process listing could not be classified for %s\n' "$area" >&2; return 1 ;;
    esac
}

check_permissions() {
    target=$1
    parent=$2
    [ -w "$parent" ] || { printf 'parent directory is not writable: %s\n' "$parent" >&2; return 1; }
    if [ -d "$target" ] && [ ! -L "$target" ]; then
        find "$target" -type d -exec sh -c 'for directory do [ -w "$directory" ] || exit 1; done' sh {} + >/dev/null 2>&1 || {
            printf 'selected tree cannot be fully inspected or removed: %s\n' "$target" >&2
            return 1
        }
    fi
    return 0
}

# Preflight every selected area before the first removal.
capture_processes
capture_status=$?
case "$capture_status" in
    0) ;;
    1) fail 'process visibility is unavailable; no files were removed' ;;
    *) fail 'cleanup process is not visible; no files were removed' ;;
esac
if [ "$level" = distclean ]; then
    check_area_activity "$build" || fail 'activity preflight failed; no files were removed'
    check_permissions "$build" "$workspace_abs" || fail 'path preflight failed; no files were removed'
else
    for entry in "$build"/* "$build"/.[!.]* "$build"/..?*; do
        exists "$entry" || continue
        is_selected_entry "$entry" || continue
        check_area_activity "$entry" || fail 'activity preflight failed; no files were removed'
        check_permissions "$entry" "$build" || fail 'path preflight failed; no files were removed'
    done
fi

remove_area() {
    target=$1
    parent=$2
    [ ! -L "$workspace_abs" ] && [ ! -L "$build" ] || {
        printf 'pending=%s workspace/build boundary changed before removal\n' "$target" >&2
        return 1
    }
    current_workspace=$(CDPATH= cd -P "$workspace_abs" 2>/dev/null && pwd -P) || return 1
    [ "$current_workspace" = "$workspace_abs" ] || return 1
    if [ -d "$build" ]; then
        current_build=$(CDPATH= cd -P "$build" 2>/dev/null && pwd -P) || return 1
        [ "$current_build" = "$build" ] || return 1
    fi
    [ -w "$parent" ] || {
        printf 'pending=%s parent is no longer writable\n' "$target" >&2
        return 1
    }
    capture_processes || {
        printf 'pending=%s process visibility is unavailable\n' "$target" >&2
        return 1
    }
    check_area_activity "$target" || {
        printf 'pending=%s activity check failed\n' "$target" >&2
        return 1
    }
    file_sizes=$(find "$target" -type f -exec sh -c 'for file do wc -c < "$file" || exit 1; done' sh {} + 2>/dev/null) || {
        printf 'pending=%s byte inventory failed after %s prior removals\n' "$target" "$removed_count" >&2
        return 1
    }
    bytes=$(printf '%s\n' "$file_sizes" | awk '$1 ~ /^[0-9]+$/ { total += $1 } END { printf "%.0f", total }')
    rm -rf "$target" || {
        printf 'pending=%s removal failed after %s prior removals\n' "$target" "$removed_count" >&2
        return 1
    }
    removed_count=$((removed_count + 1))
    removed_bytes=$((removed_bytes + bytes))
    printf 'removed=%s bytes=%s\n' "$target" "$bytes"
    return 0
}

cleanup_interrupted() {
    printf 'pending=%s interrupted after %s prior removals\n' \
        "${current_cleanup_path:-not-started}" "${removed_count:-0}" >&2
    fail 'cleanup interrupted; inspect the pending path and repeat'
}
trap 'cleanup_interrupted' INT TERM

if [ "$level" = distclean ]; then
    current_cleanup_path=$build
    remove_area "$build" "$workspace_abs" || fail 'cleanup incomplete; inspect pending path above'
else
    for entry in "$build"/* "$build"/.[!.]* "$build"/..?*; do
        exists "$entry" || continue
        is_selected_entry "$entry" || continue
        current_cleanup_path=$entry
        remove_area "$entry" "$build" || fail 'cleanup incomplete; inspect pending path above'
    done
fi

printf 'level=%s\nselected-count=%s\nremoved-count=%s\nremoved-bytes=%s\nretained-count=%s\npending-count=0\n' \
    "$level" "$selected_count" "$removed_count" "$removed_bytes" "$retained_count"
if [ "$retained_count" -gt 0 ]; then printf 'retained=%s\n' "$tools_root"; fi
