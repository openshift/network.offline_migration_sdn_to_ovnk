.PHONY: molecule

# Also needs to be updated in galaxy.yml
VERSION = 1.0.0

SANITY_TEST_ARGS ?= --docker --color
UNITS_TEST_ARGS ?= --docker --color
PYTHON_VERSION ?= `python3 -c 'import platform; print("{0}.{1}".format(platform.python_version_tuple()[0], platform.python_version_tuple()[1]))'`

clean:
	rm -f network-offline_migration_sdn_to_ovnk-$(VERSION).tar.gz
	rm -rf $(HOME)/.ansible/collections/ansible_collections/*

build: clean
	ansible-galaxy collection build --force .

install: build
	ansible-galaxy collection install --force ./network-offline_migration_sdn_to_ovnk-*.tar.gz

sanity: install
	cd $(HOME)/.ansible/collections/ansible_collections/network/offline_migration_sdn_to_ovnk && ansible-test sanity -v --python $(PYTHON_VERSION) $(SANITY_TEST_ARGS)

lint: install
	cd $(HOME)/.ansible/collections/ansible_collections/network/offline_migration_sdn_to_ovnk && ansible-lint --profile production

test-integration-incluster:
	./ci/incluster_integration.sh

test-integration:
	./ci/test-integration.sh



