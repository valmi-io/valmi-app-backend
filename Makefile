
DOCKER = docker
BUILDX = $(DOCKER) buildx build
PLATFORMS = linux/amd64,linux/arm64
BUILDX_ARGS = --platform ${PLATFORMS} --allow security.insecure --no-cache --push
BUILDER_NAME = valmi-docker-builder

.PHONY: build-and-push

setup-buildx:
	$(DOCKER) run --privileged --rm tonistiigi/binfmt --install all
	$(BUILDX) rm $(BUILDER_NAME) || true
	$(BUILDX) create --name $(BUILDER_NAME) --driver docker-container --bootstrap --buildkitd-flags '--allow-insecure-entitlement security.insecure'
	$(BUILDX) use $(BUILDER_NAME)

build-and-push:
	$(BUILDX) $(BUILDX_ARGS)  \
		-t valmiio/valmi-app-backend:${version} \
		-t valmiio/valmi-app-backend:stable \
		-t valmiio/valmi-app-backend:latest \
		-f Dockerfile.prod .

