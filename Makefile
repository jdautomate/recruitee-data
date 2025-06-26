# Makefile for MCP server project

ENV_FILE := ./.env
IMAGE_NAME := recruitee-mcp-server
PORT := 8000
FLY_VOLUME_REGION := waw


.PHONY: set-secrets deploy build run-local run-local-fresh stop clean

## Push secrets from .env to Fly.io
set-secrets:
	@flyctl secrets import < $(ENV_FILE)
	@flyctl secrets list


deploy: set-secrets
	@flyctl deploy


create_volume:
	@flyctl volumes create documents_data --size 1 -n 1 --region $(FLY_VOLUME_REGION) -y

## Run stdio locally
stdio:
	@uv run python app/app.py --transport sse --host 0.0.0.0 --port $(PORT)

## Build the Docker image
build:
	@docker build -t $(IMAGE_NAME) .

## Run Docker locally
run-local:
	@docker run --env-file $(ENV_FILE) -p $(PORT):$(PORT) --rm --name $(IMAGE_NAME) $(IMAGE_NAME)
run-local-fresh: build run-local

## Stop Docker locally
docker-stop:
	-@docker stop $(IMAGE_NAME) || true
	-@docker rm $(IMAGE_NAME) || true

## Clean up Docker
clean:
	-@docker rmi $(IMAGE_NAME) || true