## Makefile: run Development tasks.
# This is primarily used by developers of Pygasus.
# If you don't have access to Make, you can easily use the standalone
# scripts, in the 'scripts' directory.  Make sure you are still
# in the parent working directory when executing them though,
# as they will look for information in the current directory.

# For example, if you wish to initialize all Docker images:
#     make init
# (or, if you don't have Make):
#     ./scripts/init.sh

# You will need Docker installed and started.  You can install
# Docker on Linux, Windows or Mac OS.

## Commands

# check-style: check to see if the code is propertly formatted.
check-style:
	@bash scripts/check_style.sh

# clean: remove non-tagged Docker images.
clean:
	@bash scripts/clean.sh

# coverage: run the test coverage for Pygasus
coverage:
	@bash scripts/coverage.sh

# format: Reformat the code using a linter.
format:
	@bash scripts/format.sh

# init: force-update the Docker image(s)
init:
	@bash scripts/init.sh

# shell: open a shell in a Docker container.
shell:
	@bash scripts/shell.sh

# test: run the tests in one or more Docker containers.
test:
	@bash scripts/test.sh
