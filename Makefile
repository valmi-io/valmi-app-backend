
version_file := .version

# Check if the 'VALMI_APP_BACKEND_VERSION' environment variable is set.
ifeq ($(VALMI_APP_BACKEND_VERSION),)
    $(info The 'VALMI_APP_BACKEND_VERSION' environment variable is not set. Reading it from '$(version_file)')
    version := $(shell cat $(version_file))
else
		version := $(VALMI_APP_BACKEND_VERSION)
endif

DOCKER = docker
BUILDX = $(DOCKER) buildx
BUILDER_NAME=valmi-docker-builder

.PHONY: build_and_push_valmi_app

setup-buildx:
	$(DOCKER) run --privileged --rm tonistiigi/binfmt --install all
	$(BUILDX) rm $(BUILDER_NAME) || true
	$(BUILDX) create --name $(BUILDER_NAME) --driver docker-container --bootstrap
	$(BUILDX) use $(BUILDER_NAME)

build-and-push:
	$(BUILDX) build --platform linux/amd64,linux/arm64 \
		-t valmiio/valmi-app-backend:${version} \
		-t valmiio/valmi-app-backend:stable \
		-t valmiio/valmi-app-backend:latest \
		--no-cache --push -f Dockerfile.prod .

