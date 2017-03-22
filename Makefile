IMAGE_NAME := soundcloud/project-dev-kpis

default: build

.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .

.PHONY: test
test:
	docker run \
		--entrypoint=/project-dev-kpis/dev-wrap \
		$(IMAGE_NAME) \
		--config=/project-dev-kpis/config/sample.env \
		python -m unittest discover -s /project-dev-kpis/lib -p 'test_*.py'
