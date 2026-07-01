PROJECT_NAME := $(notdir $(CURDIR))

# Shared tar excludes for heavy/generated artifacts (not secrets).
TAR_ARTIFACT_EXCLUDES := \
	--exclude='$(PROJECT_NAME)/venv' \
	--exclude='$(PROJECT_NAME)/.venv' \
	--exclude='$(PROJECT_NAME)/node_modules' \
	--exclude='$(PROJECT_NAME)/frontend/node_modules' \
	--exclude='$(PROJECT_NAME)/frontend/dist' \
	--exclude='__pycache__' \
	--exclude='.DS_Store' \
	--exclude='._*' \
	--exclude='*.pyc'

.PHONY: dev backend frontend check build test frontend-lint frontend-build \
	clean-mac clean-pycache hard-backup hard-backup-private share-backup

dev:
	npm run dev

backend:
	./venv/bin/python manage.py runserver 0.0.0.0:8000

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0

check:
	./venv/bin/python manage.py check

test:
	./venv/bin/python manage.py test tutor

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

build: frontend-build

clean-mac:
	@echo "Removing .DS_Store and AppleDouble (._*) files..."
	@find . \( -path ./venv -o -path ./.venv -o -path ./node_modules -o -path ./frontend/node_modules \) -prune -o \
		\( -name '.DS_Store' -o -name '._*' \) -print -delete

clean-pycache:
	@echo "Removing __pycache__ directories and *.pyc files..."
	@find . \( -path ./venv -o -path ./.venv -o -path ./node_modules -o -path ./frontend/node_modules \) -prune -o \
		-name '__pycache__' -type d -print -exec rm -rf {} +
	@find . \( -path ./venv -o -path ./.venv -o -path ./node_modules -o -path ./frontend/node_modules \) -prune -o \
		-name '*.pyc' -type f -print -delete

hard-backup-private:
	@BACKUP="$$(cd .. && pwd)/$(PROJECT_NAME)-private-$$(date +%Y%m%d-%H%M%S).tar.gz"; \
	cd .. && COPYFILE_DISABLE=1 tar -czf "$$BACKUP" \
		$(TAR_ARTIFACT_EXCLUDES) \
		$(PROJECT_NAME) && \
	echo "Created backup: $$BACKUP"

share-backup:
	@BACKUP="$$(cd .. && pwd)/$(PROJECT_NAME)-share-$$(date +%Y%m%d-%H%M%S).tar.gz"; \
	cd .. && COPYFILE_DISABLE=1 tar -czf "$$BACKUP" \
		$(TAR_ARTIFACT_EXCLUDES) \
		--exclude='$(PROJECT_NAME)/.env' \
		--exclude='$(PROJECT_NAME)/.git' \
		$(PROJECT_NAME) && \
	echo "Created backup: $$BACKUP"

hard-backup: share-backup
