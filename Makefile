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

test: 
	docker run --rm --entrypoint "/bin/sh" -v $(PWD)/test-data/iccs-test:/test-data -v $(PWD)/hyperflow_viz_trace:/hvt-temp hyperflowwms/viz-trace -c "cp /hvt-temp/* /usr/src/app/hyperflow_viz_trace && cd /test-data && hflow-viz-trace -s /test-data"

clean:
