.PHONY: build
build:
	python setup.py sdist

.PHONY: upload
upload:
	python setup.py sdist register upload

.PHONY: clean
clean:
	rm -rf MANIFEST build dist xivo_ws.egg-info
