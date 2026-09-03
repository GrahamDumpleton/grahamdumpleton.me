---
title: "Beyond callables in wrapture"
description: "What a wrapture binding can name that is not a call: attribute reads and writes, values held in place for a test, the content of a settings dict, callables in a registry, and generators consumed item by item."
date: 2026-09-04
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "testing"]
draft: false
---

Every example in this series so far has wrapped a call. A binding named a method, and what flowed through the call was recorded or changed. Plenty of what a test needs to control is not a call, though. An outcome stored in an attribute, an environment variable that must be set or missing, a settings dict that other modules imported by reference at import time, a formatter looked up in a registry, and a generator whose interesting behaviour is spread over its consumption. `unittest.mock` and pytest between them cover most of this with `patch.dict`, `monkeypatch.setattr`, `monkeypatch.setenv` and so on, one idiom per shape. wrapture spells all of them as bindings, which buys the same lifecycle everywhere, and in a couple of places lets the binding observe as well as hold.

## Attribute bindings

A binding on a class attribute which is not a callable is detected as attribute mode, and instead of `on_call` it has `on_get`, `on_set` and `on_delete`, one channel per operation. Under the covers it installs a data descriptor on the class, wrapping whatever was there before, so a property's getter still runs and writes still land in the instance dictionary. Take a model with a status:

```python
class Model:
    status = "draft"

    def publish(self):
        self.status = "published"

    def archive(self):
        self.status = "archived"
```

Inside a timeline, reads and writes record as `get` and `set` events on the same tape as everything else:

```python
status = wrapture.binding(Model, "status")

with wrapture.timeline(status) as tape:
    model = Model()
    model.status
    model.publish()
    model.status

    print(tape.tree())

    status.events.of_kind("set").with_value("published").assert_once()
```

```
get __main__:Model.status -> 'draft'
set __main__:Model.status = 'published'
get __main__:Model.status -> 'published'
```

That assertion says `publish()` wrote the status exactly once, without the test knowing anything about how `publish()` works inside. A `get` event records the value read in `result`, the same field a call's return value uses, and a `set` event records the value written in `value`.

The channels carry the same kinds of verb as `on_call`. `on_get.returns(value)` answers a read without touching the real attribute, `on_set.rejects()` makes a write an `AttributeError`, `on_set.validates(check)` checks a written value and lets it through, and `decorates()` takes full control with the real operation handed in as a function. A guard on state transitions, which needs the current value as well as the new one, is a `decorates()`:

```python
ALLOWED = {("draft", "published"), ("published", "archived")}

def guard(write, instance, value):
    current = instance.status
    if (current, value) not in ALLOWED:
        raise ValueError(f"cannot move from {current} to {value}")
    write(value)

status.on_set.decorates(guard)
```

With that applied, `publish()` on a fresh model works, a second `publish()` raises `cannot move from published to published`, and `archive()` then works. The real write happens through `write(value)` when the guard allows it. Attribute channels have phases too, so `on_get.returns_from([...])` can read one way for two reads and another afterwards.

Two details come up as soon as this is used on real code. An attribute assigned in `__init__` rather than defined on the class does not exist when the binding is created, so the binding takes `missing_ok=True`, and the write made in `__init__` is then recorded like any other. And when the attribute is a property whose getter does work, the `get` event is the parent of whatever that work recorded, which is exactly the question a lazy-loading bug turns on:

```python
class Account:
    def __init__(self):
        self._balance = None

    def load(self):
        return 42

    @property
    def balance(self):
        if self._balance is None:
            self._balance = self.load()
        return self._balance
```

```
get __main__:Account.balance -> 42
  __main__:Account.load()  -> 42
get __main__:Account.balance -> 42
```

The first read triggered the load and the second was served from the cache, which is what the property was written to do, and a test can now assert it.

One limit follows from the mechanism. A descriptor on a class fires for access through instances, so `Model.status` read off the class itself returns the descriptor without recording, and a class-level write replaces the descriptor outright, which the binding reports by going inactive rather than pretending. The [known limitations](https://wrapture.readthedocs.io/en/latest/known-limitations.html) page has the details.

## Module attributes

A module's plain data is detected as attribute mode too, so a constant or a flag on a module gets the same three channels. A module cannot take a descriptor directly, so while a binding on it is applied the module is given a private subclass of its type with the descriptor installed there, and the original type comes back when the last binding is removed. `isinstance(module, ModuleType)` and `inspect.ismodule()` are unaffected, and the class is named `module` so reprs read the same.

What is intercepted is access through the module object. Code that did `from config import TIMEOUT` at import time holds the value already, and reads through `vars(config)` bypass the descriptor, which is the same caveat that applies to patching a module attribute with mock.

## Value bindings

Often a test does not want to observe anything. It wants an environment variable set, a settings key changed, or a module constant lowered, for the duration of the test and then put back. That is a value binding: name the owner positionally, name the slot with `attr=` for an attribute or `item=` for a mapping entry, and say what it should hold. The pricing function below reads its configuration from all the usual places:

```python
config.SETTINGS = {"currency": "USD", "tax_rate": 0.2}
config.TIMEOUT = 30.0
config.FORMATTERS = {"plain": lambda total: f"total={total:.2f}"}

def price(amount, style="plain"):
    if "API_KEY" not in os.environ:
        raise RuntimeError("API_KEY is not configured")
    total = amount * (1 + config.SETTINGS["tax_rate"])
    formatter = config.FORMATTERS[style]
    return f"[{config.SETTINGS['currency']} within {config.TIMEOUT}s] " + formatter(total)
```

An environment variable is one entry of `os.environ`, so it is `item=`. `overrides()` holds the value while applied, and on exit the prior state comes back, whether the variable existed before or not:

```python
api_key = wrapture.binding(os.environ, item="API_KEY")

with api_key.overrides("sk_test"):
    print(price(100))

print("API_KEY" in os.environ)
```

```
[USD within 30.0s] total=120.00
False
```

The other direction is `hides()`, under which the slot is absent, which is how the missing-configuration branch gets tested even on a machine where the variable is set. `overrides(None)` cannot say that, since `None` is a value that is there. A module constant is the same shape with `attr=`, and the module can be named by import path so the test needs no import of its own:

```python
with wrapture.binding("config", attr="TIMEOUT").overrides(0.5), api_key.overrides("sk_test"):
    print(price(100))
```

```
[USD within 0.5s] total=120.00
```

A value binding holds a value and observes nothing. It has no channels, no events and no phases, and it says so if you ask for them. The two spellings differ by exactly that: `binding("config", attr="TIMEOUT")` holds, and `binding("config", "TIMEOUT")` intercepts. When the question shifts from "hold this value" to "does the retry path re-read the timeout, or did it cache it", the same location upgrades to the interception form and each read becomes an event:

```python
timeout = wrapture.binding("config", "TIMEOUT")
timeout.on_get.returns(0.5)

with timeout, wrapture.timeline() as tape, api_key.overrides("sk_test"):
    price(100)
    price(100)

print([event.kind for event in tape.for_binding(timeout)])
```

```
['get', 'get']
```

Two calls, two reads. `price()` reads the timeout every time, and the tape proves it.

Everything around bindings applies to value bindings. They are context managers, they can be suspended and resumed, `active` reports whether the slot still holds what the binding put there so a teardown can see that something else overwrote it, and the pytest plugin's leak sweep reports one left applied. In the fixture shape one binding is applied holding nothing and each test says what the slot should be, `api_key.overrides("sk_test")` in one test and `api_key.hides()` in the next.

## Mapping bindings

The settings dict has a complication. Other modules did `from config import SETTINGS` at import time, so they hold the same dict by reference, and a test that replaces `config.SETTINGS` with a new dict strands them with the old one. `mode="mapping"` on the location mutates the one dict in place and never replaces it, so every holder sees the test's content, and the original entries come back on exit in their original order:

```python
SETTINGS = config.SETTINGS      # a holder, as another module would have

settings = wrapture.binding(config, "SETTINGS", mode="mapping")

with settings.updates({"tax_rate": 0.0}), api_key.overrides("sk_test"):
    print(price(100))

with settings.overrides({"currency": "EUR", "tax_rate": 0.1}), api_key.overrides("sk_test"):
    print(price(100))

print(SETTINGS, SETTINGS is config.SETTINGS)
```

```
[USD within 30.0s] total=100.00
[EUR within 30.0s] total=110.00
{'currency': 'USD', 'tax_rate': 0.2} True
```

`updates()` merges the named keys over what is there, which is `patch.dict`'s default, and `overrides()` makes the given entries the whole content, which is `patch.dict(..., clear=True)`. Both took effect through the holder's reference and both restored it. Three dict spellings exist for three different intentions: `item=` for one entry changed or absent, `attr=` to make `config.SETTINGS` a different object with holders of the old one unaffected, and `mode="mapping"` for the one dict to hold these entries for every holder.

Bindings group, and a group applies and removes atomically, so a test that needs several of these pinned at once does it in one declaration, and as a fixture the group is a `with` around a `yield`:

```python
pinned = wrapture.bindings(
    api_key=wrapture.binding(os.environ, item="API_KEY").overrides("sk_test"),
    settings=wrapture.binding(config, "SETTINGS", mode="mapping").overrides({"currency": "EUR", "tax_rate": 0.0}),
    timeout=wrapture.binding("config", attr="TIMEOUT").overrides(0.5),
)

with pinned:
    print(price(100))
```

```
[EUR within 0.5s] total=100.00
```

## A callable held in a mapping

The formatter registry is configuration too, a callable in a dict. A value binding could swap the entry wholesale, but naming the entry with `mode="callable"` wraps it instead. The stand-in is installed in the slot, records like any bound callable, has phases like any bound callable, and the original entry comes back on removal:

```python
loud = wrapture.binding(config.FORMATTERS, item="plain", mode="callable")
loud.on_call.transforms_result(str.upper)

with loud, api_key.overrides("sk_test"):
    print(price(100))

print(config.FORMATTERS["plain"](120.0))
```

```
[USD within 30.0s] TOTAL=120.00
total=120.00
```

The real formatter ran and its result was adjusted on the way out. This reaches a handler in a dispatch table with the whole call vocabulary, which is something that previously needed the callable to be pulled out and wrapped by hand.

## Generators and iteration

A callable that returns a generator produces its values later, one at a time, as the caller iterates. That changes both what recording means and what behaviour can do. Take a paginated catalogue and two consumers, one that reads to the end and one that stops as soon as it finds what it wants:

```python
class Catalogue:
    def __init__(self, records, page_size=2):
        self.records = records
        self.page_size = page_size

    def pages(self, cursor=0):
        while cursor < len(self.records):
            yield {"cursor": cursor, "items": self.records[cursor:cursor + self.page_size]}
            cursor += self.page_size


def collect_ids(pages):
    ids = []
    for page in pages:
        ids.extend(item["id"] for item in page["items"])
    return ids


def first_match(pages, predicate):
    for page in pages:
        for item in page["items"]:
            if predicate(item):
                return item
    return None
```

A test that hands the consumer a canned list of pages proves it can add up ids and nothing else. A list is never lazy, cannot be abandoned, and cannot fail between items, so the properties a streaming consumer is written to have are exactly the ones such a test cannot check.

Binding the generator method records one event covering the whole iteration, not one per page, and the event's `items` field counts what was pulled through it. Reading to the end fills in `result` with the generator's return value, `None` here:

```python
pages = wrapture.binding(Catalogue, "pages")

with wrapture.timeline(pages) as tape:
    collect_ids(catalogue.pages())
    event = pages.events.first
    print(event.items, event.result)
```

```
3 None
```

Stopping early looks different. `first_match()` finds id 3 on the second page and returns, dropping the generator before it is exhausted. The event closes with the item count reached and no result at all, `wrapture.MISSING` rather than `None`, and no `->` in the tree, which is the honest signal that the iteration never finished:

```python
with wrapture.timeline(pages) as tape:
    first_match(catalogue.pages(), lambda item: item["id"] == 3)
    event = pages.events.first
    print(event.items, event.result is wrapture.MISSING)
```

```
2 True
```

That already answers "how far did it read" and "did it finish" without touching the consumer. Item values are deliberately not captured on the tape, since a long stream would retain every item and no policy can guess which ones matter. When a test wants to see the items, or react to them, it says so with an iterator proxy. `iterator()` creates a factory with no target, behaviour is configured on its channels, and calling the factory with a generator returns a wrapped generator applying that behaviour. Since the factory takes an iterator and returns one it slots straight into the binding's `transforms_result()`:

```python
cursors = []
outcomes = []

watch = wrapture.iterator()
watch.on_item.validates_item(lambda page: cursors.append(page["cursor"]))
watch.on_finish.validates(lambda value: outcomes.append(("finished", value)))
watch.on_abandon.notifies(lambda: outcomes.append(("abandoned", None)))

pages.on_call.transforms_result(watch)

with pages:
    collect_ids(catalogue.pages())
print(cursors, outcomes)

cursors.clear(); outcomes.clear()

with pages:
    first_match(catalogue.pages(), lambda item: item["id"] == 3)
print(cursors, outcomes)
```

```
[0, 2, 4] [('finished', None)]
[0, 2] [('abandoned', None)]
```

`on_abandon` fires when a started, unexhausted generator is closed, whether explicitly or because the consumer dropped it and the garbage collector closed it. That is the question nothing else can see asked: the loop that stopped early, the generator left half-consumed. The proxy also has `on_error` for an iteration that raised, and `on_item.transforms_item()` to rewrite each item on its way through.

An item stage that raises fails the iteration at that point, as if the generator itself had raised while producing that page, which is how to test what a consumer does when page two fails to arrive:

```python
def fail_at(position, exc):
    seen = 0

    def check(page):
        nonlocal seen
        seen += 1
        if seen == position:
            raise exc

    return check

flaky = wrapture.iterator()
flaky.on_item.validates_item(fail_at(2, OSError("page 2 failed")))
pages.on_call.transforms_result(flaky)
```

With that applied, `collect_ids()` receives the first page and then an `OSError` on the second, and a consumer written to cope with that can be tested doing so.

## One lifecycle for all of it

The thread through everything here is that whichever shape a patch takes, it is a binding, and everything that applies to a binding applies to it. It is a context manager and it has a decorator form. It groups with other bindings and the group applies and removes as one unit. It can be suspended and resumed, it knows whether it is still in place, and the pytest plugin's leak sweep reports it if a test forgets to remove it. Where the shape allows it, the same binding that holds a value can be upgraded to one that sees who reads it, and a callable pulled out of a dict gets the same phases and recording as one on a class.

The [monkey patching](https://wrapture.readthedocs.io/en/latest/monkey-patching.html) guide is the full reference for every binding mode, and the worked examples on [pinning configuration](https://wrapture.readthedocs.io/en/latest/example-pinning-configuration.html), [checking that resources are released](https://wrapture.readthedocs.io/en/latest/example-resource-hygiene.html) and [testing generators and streamed results](https://wrapture.readthedocs.io/en/latest/example-streaming-data.html) each take one of the questions above further than a blog post has room for.
