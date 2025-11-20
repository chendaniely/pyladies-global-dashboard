.PHONY: rebuild-env
rebuild-env:
	@echo "Removing existing virtual environment..."
	rm -rf .venv venv
	@echo "Creating new virtual environment and updating lock file..."
	uv lock
	@echo "Syncing virtual environment with locked dependencies..."
	uv sync
	@echo "Exporting requirements.txt..."
	uv pip compile pyproject.toml -o requirements.txt
	@echo "Environment rebuilt successfully!"
