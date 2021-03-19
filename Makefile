DIRS = wait wazo-amid-mock wazo-auth-mock wazo-confd-mock wazo-sysconfd-mock

docker-images:
	for d in $(DIRS); do cd contribs/docker/$$d && docker build -t wazoplatform/$$d . && cd ../../..; done

build:
	python setup.py sdist

upload:
	python setup.py sdist register upload

clean:
	rm -rf MANIFEST build dist xivo_ws.egg-info

.PHONY: build upload clean
