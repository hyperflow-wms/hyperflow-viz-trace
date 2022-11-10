REPO_NAME = 'viz-trace'
PREFIX = 'hyperflowwms'
TAG = $(shell git describe --tags --always)

all: push

container: image

image:
	docker build -t $(PREFIX)/$(REPO_NAME) . # Build new image and automatically tag it as latest
	docker tag $(PREFIX)/$(REPO_NAME) $(PREFIX)/$(REPO_NAME):$(TAG)  # Add the version tag to the latest image

push: image
	docker push $(PREFIX)/$(REPO_NAME) # Push image tagged as latest to repository
	docker push $(PREFIX)/$(REPO_NAME):$(TAG) # Push version tagged image to repository (since this image is already pushed it will simply create or update version tag)

test: image
	docker run --rm --entrypoint "/bin/sh" -v $(PWD)/test-data/montage2_d3.0_logs:/test-data hyperflowwms/viz-trace -c "cd /test-data && hflow-viz-trace -s /test-data"

clean:
