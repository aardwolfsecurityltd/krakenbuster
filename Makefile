.PHONY: install clean run

install:
	pip install -e .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf output/ build/ dist/ *.egg-info

run:
	python -m krakenbuster
