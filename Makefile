# SPDX-License-Identifier: Apache-2.0
.DEFAULT_GOAL := help
WORKSPACE ?= $(CURDIR)
UV ?= uv

.PHONY: help package dev matrix-list matrix-build matrix-check mostlyclean clean distclean

help:
	@printf '%s\n' \
	  'HumanMotionLib repository workflows' \
	  '' \
	  'Clone requires git. GNU Make 3.81+ and a POSIX shell read this help.' \
	  'Supported host workflows: macOS arm64 and Ubuntu 24.04 x64; native Windows unsupported, WSL unverified.' \
	  'Cleanup also needs ps, lsof, find, wc, awk, grep, basename and rm.' \
	  'Required to prepare/build/check: uv 0.11.21 or newer and network access on first setup.' \
	  'CI pins uv 0.13.5; CPython 3.14 and locked dependencies are installed by uv.' \
	  'Rendering additionally requires macOS arm64 Blender 5.2.2 LTS (build d13f752e3b9c).' \
	  '' \
	  'Goals:' \
	  '  make package       build wheel and sdist, compare contents, check package' \
	  '  make dev           prepare the current library and validate sources' \
	  '  make matrix-list   list the fixed character/height preview choices' \
	  '  make matrix-build CHARACTER=male HEIGHT=1.70' \
	  '                     prepare and build one selected preview (requires Blender)' \
	  '  make matrix-check CHARACTER=male HEIGHT=1.70' \
	  '                     check an existing preview without rebuilding it' \
	  '  make mostlyclean   remove temporary and intermediate work' \
	  '  make clean         also remove ordinary generated results' \
	  '  make distclean     also remove project-prepared tools and caches' \
	  'Cleanup removes all contents in its selected build area, including unknown files and local history.' \
	  'Git sources and dist releases are outside the clean/distclean areas.' \
	  '' \
	  'Package and dev need no arguments. Matrix build/check require CHARACTER and HEIGHT.' \
	  'All paths, cache locations, versions and default recipes come from project settings.'

package:
	@sh tools/repository.sh package "$(WORKSPACE)" "$(UV)"

dev:
	@sh tools/repository.sh dev "$(WORKSPACE)" "$(UV)"

matrix-list:
	@printf '%-10s %-8s %s\n' CHARACTER HEIGHT RESULT
	@for character in skeleton male female; do \
	  for height in 150 170 190; do \
	    case "$$height" in 150) stature=1.50 ;; 170) stature=1.70 ;; 190) stature=1.90 ;; esac; \
	    printf '%-10s %-8s %s/build/automate-build-and-verification-matrix_r1_dev_current_%s-h%s\n' \
	      "$$character" "$$stature" "$(WORKSPACE)" "$$character" "$$height"; \
	  done; \
	done

matrix-build:
	@if [ -z "$(CHARACTER)" ] || [ -z "$(HEIGHT)" ]; then \
	  printf '%s\n' 'Choose CHARACTER and HEIGHT. Run `make matrix-list` for supported pairs.' >&2; \
	  exit 2; \
	fi
	@sh tools/repository.sh matrix-build "$(WORKSPACE)" "$(UV)" "$(CHARACTER)" "$(HEIGHT)"

matrix-check:
	@if [ -z "$(CHARACTER)" ] || [ -z "$(HEIGHT)" ]; then \
	  printf '%s\n' 'Choose CHARACTER and HEIGHT. Run `make matrix-list` for supported pairs.' >&2; \
	  exit 2; \
	fi
	@sh tools/repository.sh matrix-check "$(WORKSPACE)" "$(UV)" "$(CHARACTER)" "$(HEIGHT)"

mostlyclean:
	@sh tools/repository.sh mostlyclean "$(WORKSPACE)" "$(UV)"

clean:
	@sh tools/repository.sh clean "$(WORKSPACE)" "$(UV)"

distclean:
	@sh tools/repository.sh distclean "$(WORKSPACE)" "$(UV)"
