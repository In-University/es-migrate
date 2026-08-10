#!/usr/bin/env python3
"""
routes_registry.py - Script sinh file cấu hình JSON mẫu (Generator Helper).
"""

import json
import os


def generate_sample_configs(output_dir: str = "configs"):
    domains = [
        ("ecommerce", ["products", "categories", "discounts", "reviews"]),
        ("iam", ["users", "roles", "permissions", "sessions"]),
        ("billing", ["invoices", "payments", "subscriptions", "payouts"]),
        ("logistics", ["orders", "shipments", "packages", "warehouses"]),
        ("cms", ["posts", "comments", "pages", "media"]),
        ("notifications", ["emails", "sms", "webhooks", "templates"]),
        ("analytics", ["events", "metrics", "reports", "funnels"])
    ]

    route_id = 1
    total_generated = 0

    for domain_name, resources in domains:
        domain_dir = os.path.join(output_dir, domain_name)
        os.makedirs(domain_dir, exist_ok=True)
        
        for res in resources:
            specs = []
            for i in range(1, 11):
                base_path = f"/api/v{(route_id % 3) + 1}/{domain_name}/{res}-{route_id}"
                es_index = f"{domain_name}_{res.replace('-', '_')}_{route_id}"
                spec = {
                    "base_path": base_path,
                    "es_index": es_index,
                    "create_payload": {
                        "id": f"{res[:3]}-{route_id}",
                        "name": f"Sample {res} #{route_id}",
                        "status": "ACTIVE",
                        "amount": route_id * 15.0
                    },
                    "update_payload": {
                        "name": f"Sample {res} #{route_id} UPDATED",
                        "status": "ACTIVE",
                        "amount": route_id * 30.0
                    },
                    "patch_payload": {
                        "status": "INACTIVE"
                    },
                    "es_checks": {
                        "create": { "status": "ACTIVE", "amount": route_id * 15.0 },
                        "update": { "status": "ACTIVE", "amount": route_id * 30.0 },
                        "patch": { "status": "INACTIVE" },
                        "delete": { "is_deleted": True }
                    }
                }
                specs.append(spec)
                route_id += 1
                total_generated += 1

            file_path = os.path.join(domain_dir, f"{res}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(specs, f, indent=2)

    print(f"[SUCCESS] Generated {total_generated} API route configs into '{output_dir}/'")


if __name__ == "__main__":
    generate_sample_configs()
