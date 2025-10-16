.PHONY: setup install run-generate run-score run-filter run-train-d2c run-train-c2d run-iterate run-eval

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

install:
	pip install -U pip && pip install -r requirements.txt

run-generate:
	python -m evoselfcode.cli generate --config configs/generation.yaml

run-score:
	python -m evoselfcode.cli score --config configs/generation.yaml

run-filter:
	python -m evoselfcode.cli filter --config configs/generation.yaml

run-train-d2c:
	python -m evoselfcode.cli train-d2c --config configs/train_d2c.yaml

run-train-c2d:
	python -m evoselfcode.cli train-c2d --config configs/train_c2d.yaml

run-iterate:
	python -m evoselfcode.cli iterate --config configs/iterate.yaml

run-eval:
	python -m evoselfcode.cli eval --benchmark humaneval --ckpt checkpoints/latest

