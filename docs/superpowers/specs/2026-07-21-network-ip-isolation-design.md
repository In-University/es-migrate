# Network + reserved-IP isolation — design

## Problem

`terraform/main.tf` currently owns the VPC (`google_compute_network.vpc`), the
subnet (`google_compute_subnetwork.subnet`), and the two reserved internal IPs
(`google_compute_address.es6_internal`, `es9_internal`) in the same state as
the two benchmark VMs. Because `terraform destroy` operates on the entire
state regardless of module nesting, tearing down the VMs (the normal
end-of-benchmark step) also deletes the network and the reserved IPs. Any new
benchmark run then gets new IPs, and anything that depended on the old
addresses (e.g. a future rollback cluster attaching to the same subnet) has
nothing stable to point at.

## Goal

Make the VPC, subnet, and the two reserved internal IPs survive
`terraform destroy` of the benchmark infrastructure, while keeping the rest of
the workflow (`terraform apply`/`destroy` for the VMs) unchanged in spirit.

## Design

### New root config: `terraform/network/`

A second, independent Terraform root (own `terraform init`, own local state
file `terraform/network/terraform.tfstate`) that owns:

- `google_compute_network.vpc` (`es-migrate-vpc`)
- `google_compute_subnetwork.subnet` (`es-subnet`, `var.subnet_cidr`)
- `google_compute_address.es6_internal` / `es9_internal` (`INTERNAL` type,
  bound to the subnet, same fixed addresses as today:
  `10.146.0.10` / `10.146.0.11`)

Outputs: `vpc_id`, `vpc_self_link`, `subnet_id`, `subnet_self_link`,
`es6_internal_ip`, `es9_internal_ip`.

This config is applied once, independently, and is not part of the normal
benchmark apply/destroy cycle. `terraform destroy` is never run inside
`terraform/network/`.

**Why the VPC/subnet move too, not just the addresses:** a GCP `INTERNAL`
reserved address holds a reference to the subnet it was reserved in. If the
subnet stayed in the main state while only the addresses moved out, deleting
the subnet (as part of a main-infra destroy) would fail or be blocked by GCP
because live address reservations still reference it. Moving the whole
network layer (VPC + subnet + addresses) into the isolated module removes
that dependency conflict entirely — main infra never owns anything the
network layer depends on.

### Main root: `terraform/` (unchanged directory, modified contents)

`main.tf` no longer declares `google_compute_network.vpc`,
`google_compute_subnetwork.subnet`, or the two `google_compute_address`
resources. Instead:

```hcl
data "terraform_remote_state" "network" {
  backend = "local"
  config  = { path = "${path.module}/network/terraform.tfstate" }
}
```

Every reference to the old resources is replaced with the equivalent
`data.terraform_remote_state.network.outputs.*` value:

- Firewall rules (`es-allow-internal`, `es-allow-ssh`, `es-allow-es-admin`)
  use `outputs.vpc_id` in place of `google_compute_network.vpc.id`.
- VM `network_interface` blocks use `outputs.subnet_id` and
  `outputs.es6_internal_ip` / `outputs.es9_internal_ip` in place of the old
  resource attributes.
- `startup-es9.sh.tpl`'s `es6_internal_ip` templatefile variable is sourced
  from `outputs.es6_internal_ip`.

`terraform_remote_state` (over a `data "google_compute_address"` name lookup)
was chosen because it reads the exact IDs/addresses straight from the network
state's outputs — there's only one thing to keep in sync between the two
configs (the state file path), not a set of duplicated resource-name/region
variables that could drift.

Firewall rules stay in the main root and are destroyed/recreated freely with
the rest of main infra — unlike addresses, they don't block network deletion
and hold no state worth preserving across cycles.

### Apply / destroy workflow (documented in README)

```bash
cd terraform/network && terraform init && terraform apply   # once, rarely re-run
cd terraform && terraform init && terraform apply            # per benchmark cycle
...
cd terraform && terraform destroy                            # tears down VMs only
```

`network/` state stays local (matches the project's existing local-state
convention; no new backend infrastructure required).

## Out of scope

- Remote/shared state backend (GCS) for either config — explicitly declined,
  local state kept as-is.
- Any change to VM machine types, images, or the reindex workflow.
