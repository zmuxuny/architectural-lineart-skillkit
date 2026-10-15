PYTHON ?= python
.PHONY: test demo clean

test:
	$(PYTHON) -m unittest discover -s tests -v
	node --check skills/offline-svg-color-workbench/assets/editor.js

demo:
	$(PYTHON) skills/raster-to-layered-svg/scripts/convert.py --input examples/zju/source-ai-illustration.png --out-dir dist/zju --size 3840x2160
	$(PYTHON) skills/offline-svg-color-workbench/scripts/build.py --svg dist/zju/lineart.svg --png dist/zju/lineart-transparent.png --output dist/zju/workbench.html --title 'ZJU architectural line-art (illustrative)'

clean:
	rm -rf dist
