HOTFIX: Railway 502 fix

Cause:
Railway assigns a dynamic PORT environment variable.
If the container binds only to 8000, Railway can build and start it but still return 502.

Replace:
infra/docker/api.Dockerfile

With the version in this folder, then redeploy.
