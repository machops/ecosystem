package eco_base.qyaml

import future.keywords.in

# Only enforce governance rules on documents that contain document_metadata
# (the governance block — not the K8s resource documents in multi-doc .qyaml files)

deny[msg] {
    input.document_metadata
    not input.governance_info
    msg := "Missing mandatory block: governance_info"
}

deny[msg] {
    input.document_metadata
    not input.registry_binding
    msg := "Missing mandatory block: registry_binding"
}

deny[msg] {
    input.document_metadata
    not input.vector_alignment_map
    msg := "Missing mandatory block: vector_alignment_map"
}

deny[msg] {
    input.document_metadata
    not input.document_metadata.unique_id
    msg := "Missing required field: document_metadata.unique_id"
}

deny[msg] {
    input.document_metadata
    uri := input.document_metadata.uri
    not startswith(uri, "eco-base://")
    msg := sprintf("Invalid URI format (expected eco-base://): %s", [uri])
}

deny[msg] {
    input.document_metadata
    urn := input.document_metadata.urn
    not startswith(urn, "urn:eco-base:")
    msg := sprintf("Invalid URN format (expected urn:eco-base:): %s", [urn])
}

# Namespace check: only for K8s resource documents (not governance blocks)
deny[msg] {
    not input.document_metadata
    input.kind
    ns := input.metadata.namespace
    ns != ""
    ns != "eco-base"
    ns != "eco-base-staging"
    ns != "argocd"
    ns != "monitoring"
    ns != "cert-manager"
    ns != "kube-system"
    msg := sprintf("Invalid namespace: %s (expected eco-base or eco-base-staging)", [ns])
}

warn[msg] {
    input.document_metadata
    sv := input.document_metadata.schema_version
    sv != "1.0"
    sv != "v8"
    msg := sprintf("Non-standard schema_version: %s", [sv])
}
