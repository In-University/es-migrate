# es-migrate — ES6 → ES9 remote-reindex benchmark on GCP

Stands up two Elasticsearch VMs on GCP and migrates an 8-million-document,
40-field index from **Elasticsearch 6.8.23** into **Elasticsearch 9.x** using
native **reindex-from-remote**.

| VM | Zone | Role | ES version |
|----|------|------|-----------|
| `es6-source` | `asia-northeast1-a` | migration source | 6.8.23 |
| `es9-dest`   | `asia-northeast1-b` | migration destination | 9.x (`reindex.remote.whitelist` open for es6) |

Both VMs sit in a private VPC (`10.146.0.0/24`), run ES in Docker (single-node),
and have reserved internal IPs so ES9 knows ES6's address. The VPC, subnet, and
reserved IPs live in their own Terraform state (`terraform/network/`) so they
survive `terraform destroy` of the VMs — see [Network layer](#0-network-layer-apply-once).
**Security (native realm auth) is enabled on both** — no manual setup step. The `elastic` password is
seeded at boot from `var.elastic_password`: ES9 via `ELASTIC_PASSWORD`, ES6 via a
keystore `bootstrap.password` (ES6 has no `ELASTIC_PASSWORD` env). Both use the
default **bcrypt** password hashing, so hashes are portable ES6→ES9 if you ever
migrate users. TLS is left off (plain HTTP) — throwaway benchmark on a private VPC.

> ⚠️ Restrict `your_ip` and run `terraform destroy` when finished — two
> `e2-standard-4` VMs + SSD cost money.

## Prerequisites
- `gcloud` authenticated: `gcloud auth application-default login`
- `terraform` >= 1.3, project `devhub-464904` (or override `-var project_id=...`)
- Compute Engine API enabled on the project
- For the rollback scenario only (§5): Kubernetes Engine API enabled,
  `kubectl` and `helm` installed, and at least ~2 vCPU of `CPUS_ALL_REGIONS`
  quota headroom above the 2 running ES VMs (8 vCPU) for the rollback node.
  `terraform/rollback/` deliberately uses GKE **Standard** with a single
  small (`e2-small`) node, not Autopilot — Autopilot requires a *regional*
  cluster, whose ~8 vCPU HA baseline doesn't fit a default 12-vCPU project
  quota once the 2 ES VMs are already running (see comment in
  `terraform/rollback/main.tf`). Raise your quota at
  console.cloud.google.com/iam-admin/quotas if even the small node doesn't fit

## Operations monitoring
Both VM startup scripts install and start the Google Cloud Ops Agent. Ensure the
attached VM service account can write logs and monitoring metrics to the project.

## 0. Network layer (apply once)
`terraform/network/` owns the VPC, subnet, and the two reserved internal IPs
in its **own state**, independent of the benchmark VMs. Apply it once; you
generally never touch it again (and never `terraform destroy` it — that
defeats the point of separating it out):
```bash
cd terraform/network
terraform init
terraform apply
```

## 1. Provision infrastructure (VMs)
```bash
cd terraform
terraform init
terraform apply \
  -var="your_ip=$(curl -s ifconfig.me)/32" \
  -var="elastic_password=<choose-a-strong-pw>"
```
`elastic_password` defaults to `elastic` (user `elastic` / password `elastic`) if
omitted. Give the VMs ~2–4
min to install Docker + pull images, then verify (both come up **secured**):
```bash
terraform output -raw check_es6 | bash   # -> authenticates as elastic on 6.8.23
terraform output -raw check_es9 | bash   # -> authenticates as elastic on 9.x
```

## 2. Generate 8M docs on ES6
Copy the scripts up and run the generator **on the es6 VM** (localhost = fastest):
```bash
# from the repo root on your laptop (avoid es6-source:~/ -- Windows pscp does not
# expand ~ and would create a literal "~" directory):
gcloud compute scp --zone=asia-northeast1-a --recurse scripts es6-source:/home/ADMIN/
gcloud compute ssh es6-source --zone=asia-northeast1-a
# on the VM (ES_PW is required now that security is on):
cd ~/scripts
ES_PW='elastic' python3 generate_es6.py   # tune with WORKERS=, BATCH=, TOTAL=
```
Ends with `final _count = 8000000`.

## 3. Migrate ES6 → ES9 via remote reindex
Run **on the es9 VM** (or your laptop if `enable_es_admin_ingress=true`):
```bash
# from the repo root on your laptop:
gcloud compute scp --zone=asia-northeast1-b --recurse scripts es9-dest:/home/ADMIN/
gcloud compute ssh es9-dest --zone=asia-northeast1-b
# on the VM (ELASTIC_PW auths both the ES9 API and ES9's pull from ES6):
cd ~/scripts
ELASTIC_PW='elastic' ./reindex_remote.sh   # single remote reindex ES6 -> ES9
```
It pre-creates `bench-es9`, triggers the async reindex, polls to completion, and
prints the elapsed time plus a created/failures summary. Ends by asserting
`source _count == dest _count == 8000000` with zero failures.

> Remote reindex does not support slicing (`slices=auto` is rejected; manual
> slices are silently ignored, [#136269](https://github.com/elastic/elasticsearch/issues/136269)),
> so this runs as one sequential request.

## 4. Tear down
```bash
cd terraform
terraform destroy
```
This only destroys the 2 VMs and firewall rules. The VPC, subnet, and
reserved IPs (`terraform/network/`) are untouched — the next `terraform apply`
in `terraform/` picks up the same internal IPs again.

## 5. Rollback: bring ES9's changes back to ES6

Scenario: blue-green cutover already moved traffic to ES9, and it needs to be
reversed. ES6 stopped receiving writes at cutover, so it's missing anything
created, updated, or deleted on ES9 since then. This is a **one-shot,
on-demand** catch-up (not continuous replication): creates/updates go through
a small, ephemeral single-node GKE cluster running the official
`elastic/logstash` Helm chart, deletes go through a separate ID-diff
reconciliation script — both stood up/run only for the duration of the
rollback. No mapping or application change is required for either path.
Design details:
[docs/superpowers/specs/2026-07-21-es9-es6-rollback-design.md](docs/superpowers/specs/2026-07-21-es9-es6-rollback-design.md),
mapping notes: [docs/MAPPING-DIFFERENCES.md](docs/MAPPING-DIFFERENCES.md).

> **For a real rollback, use `scripts/es_rollback.sh` instead of the manual
> sequence below.** It runs the same two steps in the right order behind a
> hard gate (an incomplete delta sync can never reach the delete pass),
> checkpoints every page so it can resume, journals each document before
> overwriting or deleting it so `undo` can put ES6 back, and refuses to
> delete on a truncated id export. Full guide:
> [docs/ES-ROLLBACK.md](docs/ES-ROLLBACK.md).
>
> The `rollback_sync.sh` + `reconcile_deletes.sh` pair below stays as the
> minimal illustration of the two mechanisms (Logstash delta, id-diff
> reconciliation) and for exercising the GKE path.

The full loop is cheap to try end-to-end on a handful of documents instead of
the 8M-doc benchmark set:

```bash
# 0. Seed a tiny ES6 dataset instead of the usual 8M (from the es6 VM, §2)
TOTAL=10 WORKERS=1 ES_PW='<elastic_password>' python3 generate_es6.py

# 1. Migrate it to ES9 as usual (§3) -- also writes the cutover marker
ELASTIC_PW='<elastic_password>' ./reindex_remote.sh

# 2. Simulate post-cutover activity on ES9: a few creates, updates, hard deletes
ES9_URL=http:localhost:9200 ES_PW='elastic' MUTATE_PCT=0.1 python3 simulate_es9_mutations.py

# 3. Stand up the rollback cluster (attaches to the same VPC/subnet as the ES VMs)
cd ../terraform/rollback
terraform init
terraform apply
eval "$(terraform output -raw get_credentials)"   # configures kubectl

# 4. Sync creates/updates (reads the cutover marker automatically)
cd ../../scripts
ES6_URL=http://<es6-external-ip>:9200 ES9_URL=http://<es9-external-ip>:9200 \
ES6_INTERNAL=<es6-internal-ip> ES9_INTERNAL=<es9-internal-ip> \
ELASTIC_PW='<elastic_password>' \
./rollback_sync.sh
# watch it drain, then:

# 5. Sync deletes (the Logstash pipeline above can't see hard deletes)
ES6_URL=http://<es6-external-ip>:9200 ES9_URL=http://<es9-external-ip>:9200 \
ELASTIC_PW='<elastic_password>' \
./reconcile_deletes.sh

# 6. Verify bench-es6's count matches bench-es9's, then flip traffic back to ES6.

# 7. Tear down
helm uninstall es-rollback
cd ../terraform/rollback
terraform destroy
```

`scripts/reindex_remote.sh` (§3) writes the cutover marker — after a
successful reindex it sets `_meta.cutover_at` on `bench-es9`, an ISO-8601
timestamp `rollback_sync.sh` reads automatically as its `updated_at` lower
bound. No operator has to remember or supply it manually.

`scripts/reconcile_deletes.sh` closes the one gap a delta-by-`updated_at`
sync structurally can't: hard deletes leave no trace for it to find. It
diffs the two indices' live `_id` sets directly and deletes the difference
from ES6 — no soft-delete field, no application change.

`rollback_sync.sh` passes ES6/ES9 hosts, credentials, and the cutover marker
straight into the Helm release as literal `extraEnvs` via `--set-string` —
there's no Kubernetes Secret created or cleaned up. That's an explicit
tradeoff for this benchmark project (no existing secret-manager infra to
integrate with, plain-HTTP ES already, default password `elastic`), not a
recommendation for a real production rollback path.

## Files
```
terraform/
  network/    VPC, subnet, reserved internal IPs — own state, applied once
  rollback/   ephemeral single-node GKE cluster + firewall for the rollback sync
  main.tf, variables.tf, outputs.tf, startup-*.sh.tpl   2 VMs, firewall, Docker startup scripts
scripts/
  generate_es6.py, reindex_remote.sh, mapping-es6.json, mapping-es9.json
  es_rollback.sh            ES9 -> ES6 rollback controller: delta sync, gate,
                            delete reconciliation, verify, resume, undo (§5)
                            -- needs jq; see docs/ES-ROLLBACK.md
  test_es_rollback.sh       tests for the above -- no real cluster needed
  fake_es.py                test-only: in-memory stand-in for the ES API
  rollback_sync.sh          ES9 -> ES6 create/update delta sync orchestration (§5)
  reconcile_deletes.sh      ES9 -> ES6 delete reconciliation, ID-diff based (§5)
  simulate_es9_mutations.py test-only: create/update/delete activity on ES9 (§5)
docs/
  ES-ROLLBACK.md           guide for scripts/es_rollback.sh
  MAPPING-DIFFERENCES.md   ES6 vs ES9 mapping differences
  superpowers/specs/       design docs for the network split and rollback scenario
```

## How the remote whitelist works
ES9's container gets `-e reindex.remote.whitelist=10.146.0.10:9200` (the es6
internal IP, injected by Terraform). Without it, ES9 rejects the remote source
with a *"not whitelisted"* 400. The `es-allow-internal` firewall rule permits
tcp 9200 between the VMs so ES9 can actually reach ES6.


# Output Note
es6_internal_ip = "10.146.0.10"
es9_internal_ip = "10.146.0.11"
gke_pods_range_name = "gke-pods"
gke_services_range_name = "gke-services"
subnet_cidr = "10.146.0.0/24"
subnet_id = "projects/devhub-464904/regions/asia-northeast1/subnetworks/es-subnet"
subnet_self_link = "https://www.googleapis.com/compute/v1/projects/devhub-464904/regions/asia-northeast1/subnetworks/es-subnet"
vpc_id = "projects/devhub-464904/global/networks/es-migrate-vpc"
vpc_name = "es-migrate-vpc"
vpc_self_link = "https://www.googleapis.com/compute/v1/projects/devhub-464904/global/networks/es-migrate-vpc"


check_es6 = <sensitive>
check_es9 = <sensitive>
elastic_user = "elastic"
es6_external_ip = "34.104.220.90"
es6_internal_ip = "10.146.0.10"
es9_external_ip = "34.146.82.168"
es9_internal_ip = "10.146.0.11"
ssh_es6 = "gcloud compute ssh es6-source --zone=asia-northeast1-a --project=devhub-464904"
ssh_es9 = "gcloud compute ssh es9-dest --zone=asia-northeast1-b --project=devhub-464904"

export ES6_EXT=34.104.220.90
export ES6_INT=10.146.0.10
export ES9_EXT=34.146.82.168
export ES9_INT=10.146.0.11


gcloud compute scp --zone=asia-northeast1-a --recurse scripts es6-source:/home/ADMIN/
gcloud compute ssh es6-source --zone=asia-northeast1-a
# trên VM:
cd ~/scripts
TOTAL=10 WORKERS=1 ES_PW='elastic' python3 generate_es6.py

ELASTIC_PW='elastic' ./reindex_remote.sh

ES9_URL="http://34.146.82.168:9200" ES_PW='elastic' python3 /home/ADMIN/scripts/simulate_es9_mutations.py

curl -s -u elastic:elastic \
  -X GET "http://localhost:9200/bench-es9/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "_source": false,
    "query": {
      "match_all": {}
    },
    "size": 100
  }' | jq -r '.hits.hits[]._id'
Old
doc-1
doc-3
doc-4
doc-6
doc-8
doc-9
doc-0
doc-2
doc-5
doc-7

New
ADMIN@es9-dest:~/scripts$ ES9_URL="http://34.146.82.168:9200" ES_PW='elastic' py                         thon3 /home/ADMIN/scripts/simulate_es9_mutations.py
>> creating 3 new docs
   created doc-10
   created doc-11
   created doc-12
>> updating 3 existing docs
   updated doc-1
   updated doc-7
   updated doc-3
>> hard-deleting 2 existing docs
   deleted doc-0
   deleted doc-5
>> done. bench-es9 now has creates/updates/deletes not yet reflected on ES6.
>> next: run rollback_sync.sh (creates/updates) then reconcile_deletes.sh (delet                         es).

doc-1
doc-7
doc-3
doc-4
doc-6
doc-8
doc-9
doc-10
doc-11
doc-2
doc-12


// On Local Machine
cd ../../scripts
export ES6_EXT=34.104.220.90
export ES6_INT=10.146.0.10
export ES9_EXT=34.146.82.168
export ES9_INT=10.146.0.11
chmod +x ./rollback_sync.sh
ES6_URL="http://${ES6_EXT}:9200" ES9_URL="http://${ES9_EXT}:9200" \
ES6_INTERNAL="${ES6_INT}" ES9_INTERNAL="${ES9_INT}" \
ELASTIC_PW='elastic' \
./rollback_sync.sh


ES6_URL="http://${ES6_EXT}:9200" ES9_URL="http://${ES9_EXT}:9200" \
ELASTIC_PW='elastic' \
./reconcile_deletes.sh

sudo mkdir -p /data/rollback
sudo chown -R $USER:$USER /data

export STATE_DIR=/data/rollback
export ES6_URL=http://10.146.0.10:9200
export ES9_URL=http://10.146.0.11:9200
export ELASTIC_PW='elastic'
export REMOVE_FIELDS=modified_at
./es_rollback_py.sh run
