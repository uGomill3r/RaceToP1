# Makefile
.PHONY: build dev

# Compila el frontend dentro de Docker (no necesita npm local)
build:
	docker compose --profile build run --rm frontend-builder

# Levanta nginx sirviendo el build estático
dev:
	docker compose up frontend

# Build + serve en un solo comando
start: build dev