from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class KernelError(RuntimeError):
    """Raised when PROMPTS v2 kernel invariants are violated."""


REQUIRED_MODULE_FIELDS = {
    "module_id", "version", "title", "classification", "status", "source_refs",
    "purpose", "applies_to", "does_not_apply_to", "inputs", "outputs",
    "context_cost", "default_include", "hard_rules", "checks", "failure_conditions",
}

TASK_TAGS: dict[str, set[str]] = {
    "research": {
        "research", "empirical research", "exploratory research", "public-data research",
        "factual writing", "model-mediated tasks", "long-running projects",
        "multi-phase projects",
    },
    "software": {
        "software", "software development", "automation", "tool integrations",
        "model-mediated tasks", "long-running projects", "multi-phase projects",
    },
    "time-series": {
        "time-series research", "policy shock analysis", "research", "empirical research",
        "model-mediated tasks", "long-running projects", "multi-phase projects",
    },
    "benchmarking": {
        "benchmarking", "evaluation", "optimization", "model-mediated tasks",
        "long-running projects", "multi-phase projects",
    },
    "writing": {
        "writing", "factual writing", "publication", "model-mediated tasks",
        "long-running projects",
    },
    "creative": {
        "creative-production", "creative work", "creative design", "personal creative work",
        "product design", "model-mediated tasks",
    },
}

TERMINAL_AUTHORITIES = {
    "enforced_security_boundary",
    "explicit_user_contract",
    "deterministic_completion_check",
    "independent_evaluator",
    "human_or_policy_approval",
}


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KernelError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise KernelError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise KernelError(f"expected JSON object in {path}")
    return value


def catalog_modules(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    modules = catalog.get("modules")
    if not isinstance(modules, list):
        raise KernelError("catalog.modules must be an array")
    return modules


def validate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    modules = catalog_modules(catalog)
    declared_count = catalog.get("module_count")
    if declared_count != len(modules):
        raise KernelError(
            f"catalog module_count={declared_count!r} but contains {len(modules)} modules"
        )

    seen: set[str] = set()
    profile_specific_defaulted: list[str] = []
    heuristic_defaulted: list[str] = []

    for index, module in enumerate(modules):
        if not isinstance(module, dict):
            raise KernelError(f"module at index {index} is not an object")
        missing = REQUIRED_MODULE_FIELDS - module.keys()
        if missing:
            raise KernelError(
                f"{module.get('module_id', index)!r} missing fields: {sorted(missing)}"
            )

        module_id = module["module_id"]
        if not isinstance(module_id, str) or "." not in module_id:
            raise KernelError(f"invalid module_id: {module_id!r}")
        if module_id in seen:
            raise KernelError(f"duplicate module_id: {module_id}")
        seen.add(module_id)

        if module["status"] == "PROFILE_SPECIFIC" and module["default_include"]:
            profile_specific_defaulted.append(module_id)
        if module["classification"] == "HEURISTIC" and module["default_include"]:
            heuristic_defaulted.append(module_id)

        refs = module["source_refs"]
        if not isinstance(refs, list) or not refs:
            raise KernelError(f"{module_id} must have source_refs")
        for ref in refs:
            if not isinstance(ref, dict):
                raise KernelError(f"{module_id} has invalid source reference")
            path = ref.get("path", "")
            digest = ref.get("sha256", "")
            if not isinstance(path, str) or not path.startswith("legacy/"):
                raise KernelError(f"{module_id} source must be under legacy/: {path!r}")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)
            ):
                raise KernelError(f"{module_id} has invalid SHA-256 source digest")

    if profile_specific_defaulted:
        raise KernelError(
            "PROFILE_SPECIFIC modules cannot default-load: "
            + ", ".join(profile_specific_defaulted)
        )
    if heuristic_defaulted:
        raise KernelError(
            "HEURISTIC modules cannot default-load: " + ", ".join(heuristic_defaulted)
        )

    serialized = json.dumps(catalog, ensure_ascii=False).lower()
    if "sure, i can help you with that" in serialized:
        raise KernelError("quarantined GEOPOL assistant tail entered active catalog")

    return {
        "module_count": len(modules),
        "unique_ids": True,
        "profile_specific_default_exclusion": True,
        "heuristic_default_exclusion": True,
        "contamination_exclusion": True,
    }


def _node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        raise KernelError("graph.nodes must be an array")
    result: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise KernelError("graph node must contain string id")
        if node["id"] in result:
            raise KernelError(f"duplicate graph node: {node['id']}")
        result[node["id"]] = node
    return result


def _requires_map(graph: dict[str, Any]) -> dict[str, set[str]]:
    nodes = _node_map(graph)
    deps = {node_id: set() for node_id in nodes}
    edges = graph.get("edges")
    if not isinstance(edges, list):
        raise KernelError("graph.edges must be an array")
    for edge in edges:
        if not isinstance(edge, dict):
            raise KernelError("graph edge must be an object")
        source = edge.get("from")
        target = edge.get("to")
        edge_type = edge.get("type")
        if source not in nodes or target not in nodes:
            raise KernelError(f"edge references unknown node: {source!r} -> {target!r}")
        if edge_type == "REQUIRES":
            deps[source].add(target)
    return deps


def _detect_cycle(deps: dict[str, set[str]]) -> list[str] | None:
    temporary: set[str] = set()
    permanent: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in permanent:
            return None
        if node in temporary:
            start = stack.index(node)
            return stack[start:] + [node]
        temporary.add(node)
        stack.append(node)
        for dependency in sorted(deps[node]):
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        temporary.remove(node)
        permanent.add(node)
        return None

    for node in sorted(deps):
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def validate_graph(graph: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    modules = {item["module_id"]: item for item in catalog_modules(catalog)}
    nodes = _node_map(graph)
    if graph.get("node_count") != len(nodes):
        raise KernelError("graph node_count does not match graph nodes")
    if set(nodes) != set(modules):
        missing = sorted(set(modules) - set(nodes))
        extra = sorted(set(nodes) - set(modules))
        raise KernelError(f"graph/catalog mismatch; missing={missing}, extra={extra}")

    deps = _requires_map(graph)
    cycle = _detect_cycle(deps)
    if cycle:
        raise KernelError("dependency cycle: " + " -> ".join(cycle))

    for edge in graph.get("edges", []):
        if edge["type"] in {"SUBORDINATE_TO", "CANNOT_OVERRIDE"}:
            source_rank = nodes[edge["from"]].get("rank")
            target_rank = nodes[edge["to"]].get("rank")
            if not isinstance(source_rank, int) or not isinstance(target_rank, int):
                raise KernelError("precedence edge nodes require integer rank")
            if source_rank <= target_rank:
                raise KernelError(
                    f"invalid precedence edge {edge['from']} -> {edge['to']}: "
                    f"source rank {source_rank} must be lower authority than "
                    f"target rank {target_rank}"
                )

    return {
        "node_count": len(nodes),
        "catalog_ids_match": True,
        "edges_reference_existing_nodes": True,
        "requires_acyclic": True,
        "precedence_edges_valid": True,
    }


def _is_applicable(module: dict[str, Any], tags: set[str]) -> bool:
    applies = {_norm(value) for value in module.get("applies_to", [])}
    excludes = {_norm(value) for value in module.get("does_not_apply_to", [])}
    normalized_tags = {_norm(value) for value in tags}
    if excludes & normalized_tags:
        return False
    if not applies:
        return True
    return bool(applies & normalized_tags)


def _expand_dependencies(selected: set[str], deps: dict[str, set[str]]) -> set[str]:
    expanded = set(selected)
    changed = True
    while changed:
        changed = False
        for module_id in sorted(tuple(expanded)):
            for dependency in deps[module_id]:
                if dependency not in expanded:
                    expanded.add(dependency)
                    changed = True
    return expanded


def deterministic_order(selected: Iterable[str], graph: dict[str, Any]) -> list[str]:
    deps = _requires_map(graph)
    selected_set = _expand_dependencies(set(selected), deps)
    indegree = {node: 0 for node in selected_set}
    dependents = {node: set() for node in selected_set}
    for node in selected_set:
        for dependency in deps[node]:
            if dependency in selected_set:
                indegree[node] += 1
                dependents[dependency].add(node)

    ready = sorted(node for node, degree in indegree.items() if degree == 0)
    result: list[str] = []
    while ready:
        node = ready.pop(0)
        result.append(node)
        for dependent in sorted(dependents[node]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    if len(result) != len(selected_set):
        raise KernelError("selected module dependency graph contains a cycle")
    return result


def select_modules(
    catalog: dict[str, Any],
    graph: dict[str, Any],
    task_type: str,
    include: Iterable[str] = (),
    allow_profile_specific: bool = False,
) -> dict[str, Any]:
    if task_type not in TASK_TAGS:
        raise KernelError(
            f"unknown task_type {task_type!r}; choose from {sorted(TASK_TAGS)}"
        )
    modules = {item["module_id"]: item for item in catalog_modules(catalog)}
    tags = TASK_TAGS[task_type]
    selected: set[str] = set()
    reasons: dict[str, str] = {}

    for module_id, module in sorted(modules.items()):
        if (
            module["status"] == "ACTIVE"
            and module["default_include"]
            and _is_applicable(module, tags)
        ):
            selected.add(module_id)
            reasons[module_id] = "active default applicable to task"

    for module_id in include:
        if module_id not in modules:
            raise KernelError(f"unknown explicit module: {module_id}")
        module = modules[module_id]
        if module["status"] == "PROFILE_SPECIFIC" and not allow_profile_specific:
            raise KernelError(
                f"{module_id} is PROFILE_SPECIFIC and requires explicit "
                "--allow-profile-specific authorization"
            )
        if not _is_applicable(module, tags):
            raise KernelError(f"{module_id} does not apply to task_type={task_type!r}")
        selected.add(module_id)
        reasons[module_id] = "explicitly selected"

    order = deterministic_order(selected, graph)
    for module_id in order:
        reasons.setdefault(module_id, "required dependency")

    return {
        "task_type": task_type,
        "task_tags": sorted(tags),
        "selected_modules": order,
        "selection_reasons": {key: reasons[key] for key in order},
        "profile_specific_authorized": allow_profile_specific,
    }


def compose_prompt(goal: str, selection: dict[str, Any], catalog: dict[str, Any]) -> str:
    if not goal.strip():
        raise KernelError("goal cannot be empty")
    modules = {item["module_id"]: item for item in catalog_modules(catalog)}
    lines = [
        "# PROMPTS V2 COMPOSED TASK",
        "",
        "## Goal",
        "",
        goal.strip(),
        "",
        "## Selected modules",
        "",
    ]
    for module_id in selection["selected_modules"]:
        module = modules[module_id]
        lines.append(f"### {module_id} — {module['title']}")
        lines.append(module["purpose"])
        lines.append("")
        lines.append("Required rules:")
        for rule in module["hard_rules"]:
            lines.append(f"- {rule}")
        lines.append("")
    lines.extend(
        [
            "## Authority boundary",
            "",
            "These modules may guide or constrain work. They do not independently "
            "authorize permissions, contract amendments, terminal success or release.",
            "",
        ]
    )
    result = "\n".join(lines)
    if "Sure, I can help you with that" in result:
        raise KernelError("quarantined legacy content entered composed prompt")
    return result


def module_can_authorize_terminal(module: dict[str, Any]) -> bool:
    """Modules never authorize terminal state; authority remains external."""
    return False


def validate_repository(root: Path) -> dict[str, Any]:
    catalog = load_json(root / "modules/legacy-extracted/MODULE_CATALOG.json")
    graph = load_json(root / "RULE_GRAPH.json")
    return {
        "catalog": validate_catalog(catalog),
        "graph": validate_graph(graph, catalog),
        "terminal_authorities": sorted(TERMINAL_AUTHORITIES),
        "result": "PASS",
    }
