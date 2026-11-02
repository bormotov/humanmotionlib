#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
set -eu

usage() {
    printf '%s\n' 'repository.sh GOAL WORKSPACE UV [CHARACTER HEIGHT]' >&2
    exit 2
}

[ "$#" -ge 3 ] || usage
goal=$1
workspace=$2
uv=$3
character=${4-}
height=${5-}
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)

case "$workspace" in
    /*) ;;
    *) printf '%s\n' 'WORKSPACE must resolve to an absolute directory.' >&2; exit 2 ;;
esac
[ -d "$workspace" ] || { printf 'Workspace does not exist: %s\n' "$workspace" >&2; exit 2; }
# Reject a symlinked workspace boundary or any symlinked component before
# physical canonicalization. Resolving first would erase evidence that the
# caller selected the checkout through a link, and cleanup could then act on
# the target tree.
workspace_probe=
workspace_rest=${workspace#/}
while [ -n "$workspace_rest" ]; do
    workspace_component=${workspace_rest%%/*}
    if [ -n "$workspace_probe" ]; then
        workspace_probe=$workspace_probe/$workspace_component
    else
        workspace_probe=/$workspace_component
    fi
    if [ -L "$workspace_probe" ]; then
        printf 'Workspace path contains a symbolic link: %s\n' "$workspace_probe" >&2
        exit 2
    fi
    case "$workspace_rest" in
        */*) workspace_rest=${workspace_rest#*/} ;;
        *) workspace_rest= ;;
    esac
done
workspace=$(CDPATH= cd -- "$workspace" && pwd -P)

workflow_relative=$(awk '
    /^\[tool\.humanmotionlib\.workflow\]$/ { inside=1; next }
    /^\[/ { if (inside) exit }
    inside && /^tools-root[[:space:]]*=/ {
        sub(/^[^=]*=[[:space:]]*"/, "")
        sub(/".*/, "")
        print
        exit
    }
' "$repo_root/pyproject.toml")
workflow_uv_minimum=$(awk '
    /^\[tool\.humanmotionlib\.workflow\]$/ { inside=1; next }
    /^\[/ { if (inside) exit }
    inside && /^uv-minimum[[:space:]]*=/ {
        sub(/^[^=]*=[[:space:]]*"/, "")
        sub(/".*/, "")
        print
        exit
    }
' "$repo_root/pyproject.toml")
[ -n "$workflow_relative" ] || { printf '%s\n' 'Missing [tool.humanmotionlib.workflow].tools-root in pyproject.toml' >&2; exit 2; }
[ -n "$workflow_uv_minimum" ] || { printf '%s\n' 'Missing [tool.humanmotionlib.workflow].uv-minimum in pyproject.toml' >&2; exit 2; }
case "$workflow_relative" in
    /*|*..*) printf '%s\n' 'Configured tools-root must be a safe project-relative path.' >&2; exit 2 ;;
esac
case "$workflow_relative" in
    build/*) tools_child=${workflow_relative#build/} ;;
    *) printf '%s\n' 'Configured tools-root must be one direct child of build/.' >&2; exit 2 ;;
esac
case "$tools_child" in ''|*/*) printf '%s\n' 'Configured tools-root must be one direct child of build/.' >&2; exit 2 ;; esac
build_root=$workspace/build
if [ -L "$build_root" ]; then
    printf 'Workspace build boundary is a symbolic link: %s\n' "$build_root" >&2
    exit 2
fi
tools_root=$workspace/$workflow_relative
tool_env=$tools_root/environment
tool_python=$tool_env/bin/python3.14
cache_dir=$tools_root/cache
python_install_dir=$tools_root/python
preflight_tools_paths() {
    [ ! -L "$tools_root" ] || {
        printf 'Configured tools-root is a symbolic link: %s\n' "$tools_root" >&2
        return 2
    }
    if [ -d "$tools_root" ]; then
        tools_abs=$(CDPATH= cd -P "$tools_root" 2>/dev/null && pwd -P) || return 2
        case "$tools_abs/" in "$workspace/build/"*) ;; *)
            printf 'Configured tools-root resolves outside workspace build: %s\n' "$tools_root" >&2
            return 2
            ;;
        esac
    fi
    for configured_path in "$tool_env" "$cache_dir" "$python_install_dir" "$tools_root/logs"; do
        if [ -L "$configured_path" ]; then
            printf 'Configured writable path is a symbolic link: %s\n' "$configured_path" >&2
            return 2
        fi
        if [ -e "$configured_path" ]; then
            [ -d "$configured_path" ] || {
                printf 'Configured writable path is not a directory: %s\n' "$configured_path" >&2
                return 2
            }
            configured_abs=$(CDPATH= cd -P "$configured_path" 2>/dev/null && pwd -P) || return 2
            case "$configured_abs/" in "$tools_abs/"*) ;; *)
                printf 'Configured writable path resolves outside tools-root: %s\n' "$configured_path" >&2
                return 2
                ;;
            esac
        fi
    done
}
run_uv_logged() {
    stage=$1
    shift
    log=$tools_root/logs/$stage.log
    if "$uv" "$@" > "$log" 2>&1; then
        cat "$log"
    else
        status=$?
        cat "$log" >&2
        printf 'Setup stage %s failed; see %s\n' "$stage" "$log" >&2
        return "$status"
    fi
}

prepare_tools() {
    command -v "$uv" >/dev/null 2>&1 || {
        printf 'Required tool `uv` was not found. Install the documented uv version and retry.\n' >&2
        return 2
    }
    uv_version=$("$uv" --version | awk '{ print $2; exit }')
    uv_supported=$(awk -v actual="$uv_version" -v minimum="$workflow_uv_minimum" 'BEGIN {
        split(actual, a, "."); split(minimum, b, ".");
        for (i=1; i<=3; i++) { if ((a[i]+0) > (b[i]+0)) { print "yes"; exit }
            if ((a[i]+0) < (b[i]+0)) { print "no"; exit } }
        print "yes"
    }')
    [ "$uv_supported" = yes ] || {
        printf 'uv %s or newer is required; found %s.\n' "$workflow_uv_minimum" "$uv_version" >&2
        return 2
    }
    preflight_tools_paths || return $?
    mkdir -p "$tools_root"
    preflight_tools_paths || return $?
    mkdir -p "$cache_dir" "$python_install_dir" "$tools_root/logs"
    export UV_CACHE_DIR=$cache_dir
    export UV_PYTHON_INSTALL_DIR=$python_install_dir
    export UV_PROJECT_ENVIRONMENT=$tool_env
    if [ -x "$tool_python" ] && "$tool_python" -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 14))' >/dev/null 2>&1; then
        printf 'Reusing project Python environment: %s\n' "$tool_env"
    else
        run_uv_logged environment-create venv --clear --python 3.14 "$tool_env" || return $?
    fi
    run_uv_logged locked-dependencies sync --locked --no-install-project --group build --python "$tool_python" || return $?
    run_uv_logged dependency-check pip check --python "$tool_python" || return $?
}

HML_WORKFLOW_PYTHON=$tool_python
export HML_WORKFLOW_PYTHON

case "$goal" in
    mostlyclean|clean|distclean)
        exec sh "$repo_root/tools/project_cleanup.sh" --workspace "$workspace" \
            --tools-root "$workflow_relative" "$goal"
        ;;
    matrix-check)
        case "$character" in skeleton|male|female) ;; *) printf '%s\n' 'CHARACTER must be skeleton, male, or female.' >&2; exit 2 ;; esac
        case "$height" in 1.50|1.70|1.90) ;; *) printf '%s\n' 'HEIGHT must be 1.50, 1.70, or 1.90.' >&2; exit 2 ;; esac
        [ -x "$tool_python" ] || {
            printf 'Project tools are not prepared at %s. Run `make matrix-build CHARACTER=%s HEIGHT=%s`.\n' \
                "$tool_env" "$character" "$height" >&2
            exit 2
        }
        export HML_WORKFLOW_UV=$uv
        "$tool_python" "$repo_root/tools/repository_workflow.py" matrix-check \
            --workspace "$workspace" --character "$character" --height "$height"
        exit $?
        ;;
    package|dev|matrix-build)
        if [ "$goal" = matrix-build ]; then
            case "$character" in skeleton|male|female) ;; *) printf '%s\n' 'CHARACTER must be skeleton, male, or female.' >&2; exit 2 ;; esac
            case "$height" in 1.50|1.70|1.90) ;; *) printf '%s\n' 'HEIGHT must be 1.50, 1.70, or 1.90.' >&2; exit 2 ;; esac
        fi
        prepare_tools || exit $?
        export UV_CACHE_DIR=$cache_dir
        export UV_PYTHON_INSTALL_DIR=$python_install_dir
        export UV_PROJECT_ENVIRONMENT=$tool_env
        export HML_WORKFLOW_UV=$uv
        set -- "$goal" --workspace "$workspace"
        if [ -n "$character" ]; then set -- "$@" --character "$character"; fi
        if [ -n "$height" ]; then set -- "$@" --height "$height"; fi
        "$tool_python" "$repo_root/tools/repository_workflow.py" "$@"
        exit $?
        ;;
    *) usage ;;
esac
