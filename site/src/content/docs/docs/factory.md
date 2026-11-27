---
title: Factory Developer Preview
description: An optional, source-only companion for discovering agent skills, seeing where each came from, and routing a task. The host owns execution.
---

Factory is a **Developer Preview**. It helps developers discover agent skills,
see which source each one came from, and get a suggested route for a task. It
runs from a source checkout of the HyoDo repository. It is not part of the
published HyoDo package: the package on PyPI is HyoDo Core, and installing it
does not give you Factory.

## Who it is for

Developers who keep several skill folders and want to know which copy is which
before an agent loads one. If you only want HyoDo's local checks, you do not
need Factory.

## Try it from source

You need `git` and Python 3.11 or newer. Nothing is installed, no account or
other project is involved, and the commands below write only to a new
temporary directory, not to the folder you run them from.

```sh
preview="$(mktemp -d)"
git clone https://github.com/lofibrainwav/HyoDo.git "$preview/HyoDo"
cd "$preview/HyoDo"
git checkout --detach 6e7b33e9b9a6654de95b9eade7f053cf51f6e4ce
```

Then run the quickstart from the checkout root. It writes only to a new
temporary directory and never runs a skill:

[Factory quickstart](https://github.com/lofibrainwav/HyoDo/blob/main/examples/factory-loop/README.md#developer-preview-quickstart-source-checkout)

In that directory it finds two skills with the same name and different bytes,
reports them as `DIVERGENT` with `HOST_DECISION_REQUIRED`, registers one, and
routes a task to it. Identical bytes are reported as `ALIAS`. Factory does not
choose between sources; that choice belongs to you or your host.

## What works from source today

- Discovering skill folders across the roots you name.
- Reporting each source path and content hash, and flagging same-name
  conflicts.
- Suggesting which registered skills fit a task, and listing capability gaps.

A skill declares its category in its frontmatter. Without one, Factory guesses
from the name and description and falls back to `engineering`; the guess can
miss, and then a route selects nothing.

## What stays with the host

The host owns execution. Factory starts nothing on its own. It has a
host-directed run path that can launch a command you supply and check it with a
separate verifier. That path is **experimental**. It needs your own
authorization and isolation, and its verifier reports process credential
isolation as unproven.

No host is listed as verified. A configured adapter or a matching source hash
each establish one narrow fact; neither shows that a host session is connected.

## Versions

Core releases are numbered on PyPI. Factory has no package version: it is
identified by the source revision you check out, pinned above. When that
revision changes, the GitHub quickstart and this page change together.

See the [product boundary](/docs/product-boundary/) for how Factory relates to
Core.
