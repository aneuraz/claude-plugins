"""The closed schema of a fact (`[facts.schema]`): its faults, one message each.

A fact-set that is valid YAML is not yet a valid fact-set: a misspelled field is invisible
to a gate that reads only the ones it knows. With a schema, an unknown or missing field, a
status outside the closed set, an `@implemented` fact without a `check` and a duplicate id
are faults. A field the schema allows but the gate does not read (`capture`'s `timeout`)
is ignored: nothing is executed.
"""

from collections.abc import Iterable, Mapping

from claude_plugins_tools.project import FactSchema


def schema_faults(facts: Iterable[object], schema: FactSchema, seen: set[str]) -> list[str]:
    """The faults of `facts`; `seen` holds the ids met so far, across fact-sets."""
    faults: list[str] = []
    for index, fact in enumerate(facts, 1):
        if not isinstance(fact, Mapping):
            faults.append(f"entry #{index} is not a mapping")
            continue
        fact_id = str(fact.get("id", f"<entry #{index}>"))
        if schema.allowed is not None and (unknown := sorted(set(fact) - set(schema.allowed))):
            faults.append(f"{fact_id}: field(s) outside the schema: {', '.join(unknown)}")
        if missing := sorted(set(schema.required) - set(fact)):
            faults.append(f"{fact_id}: missing field(s): {', '.join(missing)}")
        status = fact.get("status")
        if schema.statuses is not None and status not in schema.statuses:
            faults.append(f"{fact_id}: unknown status {status!r}")
        if status == "@implemented" and not fact.get("check"):
            faults.append(f"{fact_id}: @implemented without a check")
        if fact_id in seen:
            faults.append(f"{fact_id}: duplicate id")
        seen.add(fact_id)
    return faults
