#!/usr/bin/env python3
"""Calculate minimum Kubernetes resource requests from manifest files."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import yaml

CPU_MILLI = 1000
MEMORY_SUFFIXES = {
    "Ki": 1024,
    "Mi": 1024**2,
    "Gi": 1024**3,
    "Ti": 1024**4,
    "Pi": 1024**5,
    "Ei": 1024**6,
    "K": 1000,
    "M": 1000**2,
    "G": 1000**3,
    "T": 1000**4,
    "P": 1000**5,
    "E": 1000**6,
    "m": 1 / 1000,
}

WORKLOAD_KINDS = {
    "Deployment",
    "StatefulSet",
    "ReplicaSet",
    "ReplicationController",
    "Job",
    "CronJob",
    "DaemonSet",
}


@dataclass
class WorkloadResource:
    namespace: str
    kind: str
    name: str
    node_group: str
    replicas: int
    cpu_millicores: int
    memory_bytes: int


def parse_cpu_millicores(raw: Optional[str]) -> int:
    if not raw:
        return 0
    value = str(raw).strip()
    if value.endswith("m"):
        return int(float(value[:-1]))
    return int(float(value) * CPU_MILLI)


def parse_memory_bytes(raw: Optional[str]) -> int:
    if not raw:
        return 0
    value = str(raw).strip()
    for suffix, multiplier in MEMORY_SUFFIXES.items():
        if value.endswith(suffix):
            number = float(value[: -len(suffix)])
            return int(number * multiplier)
    return int(float(value))


def quantity_to_resources(requests: Dict[str, str]) -> Tuple[int, int]:
    return parse_cpu_millicores(requests.get("cpu")), parse_memory_bytes(requests.get("memory"))


def pod_requests(pod_spec: Dict) -> Tuple[int, int]:
    containers = pod_spec.get("containers", []) or []
    init_containers = pod_spec.get("initContainers", []) or []

    total_cpu = 0
    total_memory = 0
    for container in containers:
        req = (container.get("resources") or {}).get("requests") or {}
        cpu, memory = quantity_to_resources(req)
        total_cpu += cpu
        total_memory += memory

    max_init_cpu = 0
    max_init_memory = 0
    for container in init_containers:
        req = (container.get("resources") or {}).get("requests") or {}
        cpu, memory = quantity_to_resources(req)
        max_init_cpu = max(max_init_cpu, cpu)
        max_init_memory = max(max_init_memory, memory)

    return max(total_cpu, max_init_cpu), max(total_memory, max_init_memory)


def node_group_key(pod_spec: Dict) -> str:
    node_selector = pod_spec.get("nodeSelector") or {}
    affinity = (pod_spec.get("affinity") or {}).get("nodeAffinity") or {}
    required = affinity.get("requiredDuringSchedulingIgnoredDuringExecution") or {}
    terms = required.get("nodeSelectorTerms") or []

    selector_part = ",".join(f"{k}={v}" for k, v in sorted(node_selector.items()))
    term_values = []
    for term in terms:
        exprs = term.get("matchExpressions") or []
        expr_values = []
        for expr in exprs:
            key = expr.get("key", "")
            op = expr.get("operator", "")
            vals = ",".join(sorted(str(v) for v in expr.get("values", []) or []))
            expr_values.append(f"{key}:{op}:{vals}")
        term_values.append("&".join(sorted(expr_values)))

    affinity_part = "|".join(sorted(term_values))

    if not selector_part and not affinity_part:
        return "default"

    parts = []
    if selector_part:
        parts.append(f"selector[{selector_part}]")
    if affinity_part:
        parts.append(f"affinity[{affinity_part}]")
    return " ".join(parts)


def doc_namespace(doc: Dict) -> str:
    return ((doc.get("metadata") or {}).get("namespace") or "default").strip() or "default"


def workload_replicas(doc: Dict) -> int:
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "Job":
        return max(int(spec.get("parallelism", 1) or 1), 1)
    if kind == "CronJob":
        tmpl_spec = ((spec.get("jobTemplate") or {}).get("spec") or {})
        return max(int(tmpl_spec.get("parallelism", 1) or 1), 1)
    if kind == "DaemonSet":
        return 1
    return max(int(spec.get("replicas", 1) or 1), 1)


def workload_pod_spec(doc: Dict) -> Dict:
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "CronJob":
        return (((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get("spec") or {}
    if kind == "Job":
        return (spec.get("template") or {}).get("spec") or {}
    return ((spec.get("template") or {}).get("spec") or {})


def load_documents(folder: Path) -> Tuple[List[Dict], int]:
    docs: List[Dict] = []
    file_count = 0
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
            continue
        file_count += 1
        with path.open("r", encoding="utf-8") as handle:
            for doc in yaml.safe_load_all(handle):
                if isinstance(doc, dict):
                    docs.append(doc)
    return docs, file_count


def build_hpa_min_replicas(docs: Iterable[Dict]) -> Dict[Tuple[str, str, str], int]:
    result: Dict[Tuple[str, str, str], int] = {}
    for doc in docs:
        if doc.get("kind") != "HorizontalPodAutoscaler":
            continue
        namespace = doc_namespace(doc)
        spec = doc.get("spec") or {}
        target = spec.get("scaleTargetRef") or {}
        target_kind = target.get("kind")
        target_name = target.get("name")
        if not target_kind or not target_name:
            continue
        min_replicas = max(int(spec.get("minReplicas", 1) or 1), 1)
        key = (namespace, str(target_kind), str(target_name))
        result[key] = min_replicas
    return result


def calculate_minimum_resources(folder: Path) -> Dict:
    docs, file_count = load_documents(folder)
    hpa_index = build_hpa_min_replicas(docs)

    workloads: List[WorkloadResource] = []
    grouped = defaultdict(lambda: {"cpu_millicores": 0, "memory_bytes": 0, "workloads": []})

    for doc in docs:
        kind = doc.get("kind")
        if kind not in WORKLOAD_KINDS:
            continue

        metadata = doc.get("metadata") or {}
        name = metadata.get("name") or "unknown"
        namespace = doc_namespace(doc)
        pod_spec = workload_pod_spec(doc)
        cpu_per_pod, memory_per_pod = pod_requests(pod_spec)

        replicas = workload_replicas(doc)
        hpa_replicas = hpa_index.get((namespace, kind, name))
        if hpa_replicas is not None:
            replicas = hpa_replicas

        node_group = node_group_key(pod_spec)

        total_cpu = cpu_per_pod * replicas
        total_memory = memory_per_pod * replicas

        workload = WorkloadResource(
            namespace=namespace,
            kind=kind,
            name=name,
            node_group=node_group,
            replicas=replicas,
            cpu_millicores=total_cpu,
            memory_bytes=total_memory,
        )
        workloads.append(workload)

        grouped[node_group]["cpu_millicores"] += total_cpu
        grouped[node_group]["memory_bytes"] += total_memory
        grouped[node_group]["workloads"].append(
            {
                "namespace": namespace,
                "kind": kind,
                "name": name,
                "replicas": replicas,
                "cpu_millicores": total_cpu,
                "memory_bytes": total_memory,
            }
        )

    grand_cpu = sum(item.cpu_millicores for item in workloads)
    grand_mem = sum(item.memory_bytes for item in workloads)

    return {
        "folder": str(folder),
        "summary": {
            "yaml_files_scanned": file_count,
            "manifest_documents_scanned": len(docs),
            "workloads_considered": len(workloads),
        },
        "total": {
            "cpu_millicores": grand_cpu,
            "cpu_cores": round(grand_cpu / CPU_MILLI, 3),
            "memory_bytes": grand_mem,
            "memory_mib": round(grand_mem / (1024**2), 3),
        },
        "groups": {
            key: {
                "cpu_millicores": value["cpu_millicores"],
                "cpu_cores": round(value["cpu_millicores"] / CPU_MILLI, 3),
                "memory_bytes": value["memory_bytes"],
                "memory_mib": round(value["memory_bytes"] / (1024**2), 3),
                "workloads": value["workloads"],
            }
            for key, value in sorted(grouped.items())
        },
    }


def render_table(result: Dict) -> str:
    lines = [
        "Summary | Value",
        "---|---:",
        f"YAML files scanned | {result['summary']['yaml_files_scanned']}",
        f"Manifest documents scanned | {result['summary']['manifest_documents_scanned']}",
        f"Workloads considered | {result['summary']['workloads_considered']}",
        f"Total CPU (cores) | {result['total']['cpu_cores']:.3f}",
        f"Total Memory (Mi) | {result['total']['memory_mib']:.3f}",
        "",
        "Node Group Totals | CPU (cores) | Memory (Mi) | Workloads",
        "---|---:|---:|---:",
    ]
    for group_name, data in result["groups"].items():
        lines.append(
            f"{group_name} | {data['cpu_cores']:.3f} | {data['memory_mib']:.3f} | {len(data['workloads'])}"
        )

    lines.extend(
        [
            "",
            "Workload Details | Node Group | Namespace | Kind | Replicas | CPU (cores) | Memory (Mi)",
            "---|---|---|---|---:|---:|---:",
        ]
    )
    for group_name, data in result["groups"].items():
        for workload in sorted(data["workloads"], key=lambda item: (item["namespace"], item["kind"], item["name"])):
            lines.append(
                f"{workload['name']} | {group_name} | {workload['namespace']} | {workload['kind']} | "
                f"{workload['replicas']} | {workload['cpu_millicores'] / CPU_MILLI:.3f} | "
                f"{workload['memory_bytes'] / (1024**2):.3f}"
            )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tính minimum Kubernetes resources (CPU/Memory requests) từ folder YAML."
    )
    parser.add_argument("folder", help="Folder chứa các file .yaml/.yml")
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Định dạng output (mặc định: table)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    folder = Path(args.folder).resolve()
    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"Folder không hợp lệ: {folder}")

    result = calculate_minimum_resources(folder)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_table(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
