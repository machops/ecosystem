package main

import future.keywords.if
import future.keywords.in

# Test: deny privileged containers
test_deny_privileged_container if {
  result := deny with input as {
    "kind": "Pod",
    "metadata": {
      "name": "test-priv",
      "namespace": "platform-01"
    },
    "spec": {
      "containers": [{
        "name": "app",
        "image": "nginx:1.0",
        "securityContext": {"privileged": true}
      }]
    }
  }
  count(result) > 0
}

# Test: allow non-privileged containers
test_allow_non_privileged if {
  result := deny with input as {
    "kind": "Pod",
    "metadata": {
      "name": "test-ok",
      "namespace": "platform-01"
    },
    "spec": {
      "containers": [{
        "name": "app",
        "image": "ghcr.io/indestructibleorg/app:1.0",
        "securityContext": {"privileged": false}
      }]
    }
  }
  count(result) == 0
}

# Test: deny unapproved registry
test_deny_unapproved_registry if {
  result := deny with input as {
    "kind": "Pod",
    "metadata": {
      "name": "test-registry",
      "namespace": "platform-01"
    },
    "spec": {
      "containers": [{
        "name": "app",
        "image": "docker.io/library/nginx:1.0"
      }]
    }
  }
  count(result) > 0
}

# Deny rule (mirrors Gatekeeper logic for testing)
deny[msg] if {
  input.kind == "Pod"
  c := input.spec.containers[_]
  c.securityContext.privileged == true
  not input.metadata.labels["policy.eco.platform/exempt"]
  msg := sprintf("Container %v is privileged", [c.name])
}

deny[msg] if {
  input.kind == "Pod"
  c := input.spec.containers[_]
  not startswith(c.image, "harbor.")
  not startswith(c.image, "ghcr.io/indestructibleorg")
  not startswith(c.image, "asia-east1-docker.pkg.dev/my-project-ops-1991")
  not startswith(c.image, "gcr.io/my-project-ops-1991")
  msg := sprintf("Container %v uses unapproved registry: %v", [c.name, c.image])
}
