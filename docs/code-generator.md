# Code Generator Architecture

This document explains how the **no-code** service converts a workflow graph into
Python source code.  It focuses on the handler interface and the mechanism used
to register new handlers.

## Handler interface

Each node in the workflow is processed by a class implementing the
`NodeHandler` interface.  The base definition lives in
`src/backend/no-code-service/node_handlers/base.py` and contains two key
methods:

- `handle(node, generator) -> str`
  
  Generates and returns the Python snippet for the supplied node.  The
  `generator` instance can be used to inspect other nodes or to register
  additional handlers at runtime.

- `required_packages() -> List[str]`
  
  Optional hook allowing a handler to declare third‑party package dependencies.
  The generator aggregates these across all nodes when producing the final
  `requirements.txt` file.

Handlers also expose a `node_type` attribute which is used as the key in the
registry.

## Handler registration

Handlers are instantiated in `node_handlers/__init__.py`.  They are collected
into the `HANDLER_REGISTRY` dictionary where the keys are the supported
`node_type` strings and the values are handler instances.  The `Generator`
initialises its internal registry from this mapping.  Additional handlers can be
added in two ways:

1. **Static registration** – add the new handler class to the list in
   `node_handlers/__init__.py` so it becomes part of `HANDLER_REGISTRY`.
2. **Runtime registration** – call `generator.register_handler(custom_handler)`
   before invoking `generate_strategy_code`.

## Fallback handler

If a workflow contains a node whose type is not present in the registry, the
`Generator` uses `FallbackHandler`.  This handler logs a warning and returns an
empty snippet, allowing generation to continue while signalling that the node
was ignored.  The behaviour ensures forward compatibility with newer workflow
features without causing failures in older deployments.

## DataFrame column conventions

All node handlers operate on a shared pandas ``DataFrame`` named ``df``. Each
handler appends a column to this frame following a simple naming scheme based on
the node's identifier:

| Node type             | Column prefix | Example column        |
|----------------------|---------------|-----------------------|
| ``dataSource``       | *(initialises ``df``)* | ``df`` loaded with data |
| ``customDataset``    | *(initialises ``df``)* | ``df`` from CSV         |
| ``technicalIndicator`` | ``feature_`` | ``feature_abcd1234``  |
| ``condition``        | ``target_``   | ``target_abcd1234``   |
| ``action``           | ``action_``   | ``action_abcd1234``   |
| ``logic``            | ``logic_``    | ``logic_abcd1234``    |
| ``risk``             | ``risk_``     | ``risk_abcd1234``     |
| ``output``           | ``output_``   | ``output_abcd1234``   |
| unknown              | ``unknown_``  | ``unknown_abcd1234``  |

Nodes are processed sequentially in the order they appear in the workflow. Data
sources initialise ``df`` first. Feature generators such as technical indicators
run next, followed by label generation via condition nodes. Remaining nodes add
their respective columns afterwards. This order ensures that downstream steps
can rely on features and targets being present when needed.
