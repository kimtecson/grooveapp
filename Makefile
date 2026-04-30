IMAGE   ?= musicapp-backend
REGION  ?= us-east-1
ACCOUNT ?= $(shell aws sts get-caller-identity --query Account --output text)

# ── Local dev ──────────────────────────────────────────────────────────────────
local:
	export $$(cat env.local | xargs) && python backend/app.py

# ── EC2 (run directly on the instance with gunicorn) ──────────────────────────
ec2:
	export $$(cat env.prod | xargs) && \
	gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 --chdir backend app:app

# ── ECS (build + push Docker image, then deploy) ──────────────────────────────
ecs-build:
	docker build -t $(IMAGE) backend/

ecs-push:
	aws ecr get-login-password --region $(REGION) | \
	docker login --username AWS --password-stdin $(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com
	docker tag $(IMAGE):latest $(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com/$(IMAGE):latest
	docker push $(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com/$(IMAGE):latest

ecs: ecs-build ecs-push

# ── Lambda (zip and deploy) ────────────────────────────────────────────────────
lambda-package:
	pip install -r backend/requirements.txt -t lambda_package/
	cp backend/app.py backend/lambda_handler.py lambda_package/
	cd lambda_package && zip -r ../lambda.zip .
	rm -rf lambda_package/

lambda-deploy: lambda-package
	aws lambda update-function-code \
		--function-name musicapp-backend \
		--zip-file fileb://lambda.zip \
		--region $(REGION)
	rm lambda.zip

# ── DB setup (local) ───────────────────────────────────────────────────────────
setup-local:
	export $$(cat env.local | xargs) && \
	python scripts/create_login_table.py && \
	python scripts/create_music_table.py && \
	python scripts/create_subscription_table.py && \
	python scripts/load_music_data.py
