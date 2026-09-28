#!/usr/bin/env python3

import tempfile
import textwrap
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k8s_minimum_resources as kmr


class K8sMinimumResourcesTests(unittest.TestCase):
    def write_yaml(self, root: Path, name: str, content: str) -> None:
        (root / name).write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def test_calculate_with_hpa_and_node_grouping(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_yaml(
                root,
                "app.yaml",
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: web
                  namespace: prod
                spec:
                  replicas: 3
                  template:
                    spec:
                      nodeSelector:
                        pool: general
                      containers:
                        - name: app
                          resources:
                            requests:
                              cpu: 250m
                              memory: 128Mi
                ---
                apiVersion: autoscaling/v2
                kind: HorizontalPodAutoscaler
                metadata:
                  name: web-hpa
                  namespace: prod
                spec:
                  minReplicas: 2
                  maxReplicas: 5
                  scaleTargetRef:
                    apiVersion: apps/v1
                    kind: Deployment
                    name: web
                """,
            )
            self.write_yaml(
                root,
                "worker.yaml",
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: worker
                  namespace: prod
                spec:
                  replicas: 1
                  template:
                    spec:
                      affinity:
                        nodeAffinity:
                          requiredDuringSchedulingIgnoredDuringExecution:
                            nodeSelectorTerms:
                              - matchExpressions:
                                  - key: dedicated
                                    operator: In
                                    values: [batch]
                      containers:
                        - name: worker
                          resources:
                            requests:
                              cpu: "1"
                              memory: 1Gi
                """,
            )

            result = kmr.calculate_minimum_resources(root)

            self.assertEqual(result["total"]["cpu_millicores"], 1500)
            self.assertEqual(result["total"]["memory_bytes"], 1342177280)

            groups = result["groups"]
            self.assertIn("selector[pool=general]", groups)
            self.assertIn("affinity[dedicated:In:batch]", groups)

            self.assertEqual(groups["selector[pool=general]"]["cpu_millicores"], 500)
            self.assertEqual(groups["selector[pool=general]"]["memory_mib"], 256.0)

            self.assertEqual(groups["affinity[dedicated:In:batch]"]["cpu_millicores"], 1000)
            self.assertEqual(groups["affinity[dedicated:In:batch]"]["memory_mib"], 1024.0)

    def test_init_container_sizing_rule(self):
        pod_spec = {
            "containers": [
                {"resources": {"requests": {"cpu": "300m", "memory": "200Mi"}}},
                {"resources": {"requests": {"cpu": "200m", "memory": "100Mi"}}},
            ],
            "initContainers": [
                {"resources": {"requests": {"cpu": "800m", "memory": "50Mi"}}}
            ],
        }

        cpu, memory = kmr.pod_requests(pod_spec)
        self.assertEqual(cpu, 800)
        self.assertEqual(memory, 314572800)


if __name__ == "__main__":
    unittest.main()
