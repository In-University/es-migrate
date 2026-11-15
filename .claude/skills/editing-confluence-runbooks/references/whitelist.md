# Link Whitelist

Every URL in runbook content (`href`, `ri:value`, and raw URLs inside code blocks) must start with one of the **URL prefix** values below. The agent checks this during self-review (not automated).

- Host-only prefix (`https://jenkins.corp/`) allows the whole host. Path prefix (`https://jenkins.corp/job/tf-apply/`) allows only that job and below.
- The Confluence base host is always allowed.
- Loopback and in-cluster addresses used inside commands are always allowed: `localhost`, `127.0.0.1`, `*.svc`, `*.svc.cluster.local`.
- A row whose URL prefix is `TODO` allows nothing. If a step needs that system → **stop and ask the user for the link**.

> ⚠️ Rows marked `EXAMPLE` use placeholder domains (`*.example.internal`) so the skill can be tested. Replace them with real values before real use.

| Key | System | URL prefix | Notes |
|---|---|---|---|
| jenkins | Jenkins server | https://jenkins.example.internal/ | EXAMPLE |
| tf-plan | Terraform plan job | https://jenkins.example.internal/job/infra/job/terraform-plan/ | EXAMPLE — run plan here first |
| tf-apply | Terraform apply job | https://jenkins.example.internal/job/infra/job/terraform-apply/ | EXAMPLE — apply after plan reviewed |
| k8s-stg | Kubernetes dashboard STG | https://k8s-stg.example.internal/ | EXAMPLE |
| k8s-prd | Kubernetes dashboard PRD | https://k8s-prd.example.internal/ | EXAMPLE |
| grafana | Monitoring (Grafana) | https://grafana.example.internal/ | EXAMPLE |
| gcp-console | GCP Console | https://console.cloud.google.com/ | |
| argocd | Argo CD | TODO | |
| kibana | Kibana / logs | TODO | |
