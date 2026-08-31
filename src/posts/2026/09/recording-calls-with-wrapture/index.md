---
title: "Recording calls with wrapture"
description: "How wrapture's timeline and tape record what real code did, and how to filter, assert on and walk that record. Worked through on a resource leak that no return value reveals."
date: 2026-09-02
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "testing"]
draft: true
---

In [unit testing with wrapture](/posts/2026/09/unit-testing-with-wrapture/) the tests leaned on a timeline and a tape to assert on what happened, and I skipped over what those actually are. This post is about the recording side of wrapture: what gets recorded, what one event holds, how a test reads the record back, and the whole-tape views that answer questions about the flow between calls rather than about any one of them.

The example is a resource leak, because it is the kind of bug the recording model was made for. Code that acquires a connection has to release it on every path out: the normal return, the early return, and the exception. The path that forgets is the one nobody looks at, and it does not fail. Nothing raises, nothing returns the wrong value, the test passes, and the pool runs dry a week later in production. The failure is an absence, and asserting on an absence needs a record of what did happen, on the real objects, including objects minted mid-call that the test never held.

## The code under test

A stand-in for any pooled resource. `Database.connect()` mints a `Connection`, and a connection answers queries until `close()` sets its `closed` flag:

```python
class Connection:
    def __init__(self, number):
        self.number = number
        self.closed = False

    def execute(self, sql):
        if self.closed:
            raise RuntimeError("connection is closed")
        return [(1, "widget")] if "id = 1" in sql else []

    def close(self):
        self.closed = True

    def __repr__(self):
        return f"<Connection {self.number}>"


class Database:
    def __init__(self):
        self.issued = 0

    def connect(self):
        self.issued += 1
        return Connection(self.issued)
```

The repository is where the bug lives. `count()` releases in a `finally`, so it is safe on every path. `find()` releases only when a row was found; the not-found early return leaks its connection:

```python
class Repository:
    def __init__(self, database):
        self.database = database

    def count(self, table):
        connection = self.database.connect()
        try:
            return len(connection.execute(f"SELECT * FROM {table}"))
        finally:
            connection.close()

    def find(self, table, key):
        connection = self.database.connect()
        rows = connection.execute(f"SELECT * FROM {table} WHERE id = {key}")
        if not rows:
            return None
        connection.close()
        return rows[0]


def report(repository, keys):
    found = [repository.find("products", key) for key in keys]
    return repository.count("products"), [row for row in found if row]
```

Running `report(Repository(Database()), [1, 2])` returns `(0, [(1, 'widget')])`, which is correct. Nothing about that result says a connection was left open.

The usual way to test this is a hand-written fake `Database` whose `connect()` appends to a list, with connections that flip a flag, and a test that walks the list. It works, but it tests a substitute. The real classes never run, the fake has to be kept in step with them, and every acquiring class in the codebase needs its own. The record you want is of the real calls.

## The timeline and the tape

Bind `connect` on `Database` and `close` on `Connection`, and record both onto one tape. Neither binding has any behaviour configured, so they observe and nothing else:

```python
connect = wrapture.binding(Database, "connect")
close = wrapture.binding(Connection, "close")

with wrapture.timeline(connect, close) as tape:
    report(Repository(Database()), [1, 2])

print(tape.tree())
```

```
__main__:Database.connect()  -> <Connection 1>
__main__:Connection.close()  -> None
__main__:Database.connect()  -> <Connection 2>
__main__:Database.connect()  -> <Connection 3>
__main__:Connection.close()  -> None
```

Three acquisitions, two releases, and reading down the tape you can already see which one has no partner.

The two words are two views of one thing. The timeline is the scope: `with wrapture.timeline(...)` opens it, the bindings handed to it are applied on entry and removed on exit, and while it is open every call through every applied binding records an event. The tape is what the scope holds. Bindings applied by other means, a fixture or an outer `with`, record onto an open tape as well, and a binding applied with no timeline open records nothing and costs almost nothing beyond wrapt's own dispatch, so leaving bindings applied and only occasionally recording is a supported pattern rather than a mistake.

Notice that `close` is bound on the `Connection` class, not on any connection object. The connections do not exist when the test starts; `connect()` mints them mid-call. A binding on the class wraps the method for every instance, present and future, which is exactly what covers objects a factory hands out. A mock injected through a seam cannot see those objects at all.

## What one event holds

Each call through a binding inside the scope records one event, and an event is a good deal richer than a mock's call record. The fields a test typically reads are `path`, the fully qualified location in `module:qualname` form; `instance`, the object the method was called on; `arguments`, the call normalised against the real signature with defaults applied, so `charge(500)` and `charge(amount=500)` record identically; `result`, the real return value, or `exception` when the call raised instead; and `seq`, `parent_id` and `depth`, which place the event in the call tree. There are timings too, `started` and `duration`, with recording's own bookkeeping excluded from the figure.

Because the values are real, they can be compared across events. A `connect` event's `result` is the connection it minted, and a `close` event's `instance` is the connection it was called on, so the leaked connections are the difference between the two sets:

```python
with wrapture.timeline(connect, close):
    report(Repository(Database()), [1, 2])

    acquired = {event.result for event in connect.events}
    released = {event.instance for event in close.events}

    print(acquired - released)
```

```
{<Connection 2>}
```

That is the whole question answered, and it needed nothing from the repository. Events record what actually flowed, behaviour included: a call stubbed with `returns()` records the stubbed result, a failure injected with `raises()` records that exception, and when `transforms_args()` rewrote the arguments the event keeps both the arguments as the caller sent them and the ones the real method received, which no substitution-based tool can record because replacing a function discards what it would have been called with.

## Filters narrow, assertions conclude

A binding's `events` property is a filterable view over the tape for that one binding, and it works inside the `with` block after the code under test has run. One naming rule holds across the whole package: a method whose name starts with `assert_` raises immediately, one starting with `expect_` declares and is checked when the scope closes, and everything else returns data. A mistyped assertion name is therefore an `AttributeError` rather than the silent pass mock's `assert_calld_once` was famous for.

Filters chain and never raise. `with_args(amount=500)` keeps calls whose normalised arguments include the given values, `with_instance(obj)` keeps calls made on exactly that object by identity, `raising(TimeoutError)` keeps calls that raised, `returning(value)` keeps calls that returned it, and `matching(predicate)` is the escape hatch. Assertions then conclude: `assert_never()`, `assert_once()`, `assert_times(n)`, `assert_at_least(n)` and `assert_at_most(n)`. Each returns the log on success so a passing assertion can keep chaining, and each prints the events it looked at on failure. Asserting three closes when there were two gives:

```
AssertionError: expected exactly 3 event(s), got 2
<EventLog __main__:Connection.close: 2 event(s)>
    __main__:Connection.close()
    __main__:Connection.close()
```

An assertion is written where it runs. An expectation is the same claim declared on the binding up front, before the run, and verified when the timeline exits:

```python
close = wrapture.binding(Connection, "close").expect_times(3)

with wrapture.timeline(connect, close):
    report(Repository(Database()), [1, 2])
```

```
ExpectationNotMetError: declared expectation on __main__:Connection.close not met: expected exactly 3 event(s), got 2
<EventLog __main__:Connection.close: 2 event(s)>
    __main__:Connection.close()
    __main__:Connection.close()
```

`ExpectationNotMetError` derives from `AssertionError`, so test frameworks report it as a failure. Expectations read as a contract at the top of the test with the body free of bookkeeping, and an expectation with nothing recording is an error rather than a pass. Verification is skipped when the block itself raised, since the in-flight failure is the real cause and a verification error on top would bury it.

## The tree names the culprit

Counting says something leaked, and pairing says what. To say who, add the repository methods to the timeline. The tape then nests each acquire and release under the method that made it, and `tape.children_of()` walks the tree, so a root whose children include a `connect` but no `close` names itself:

```python
find = wrapture.binding(Repository, "find")
count = wrapture.binding(Repository, "count")

with wrapture.timeline(find, count, connect, close) as tape:
    report(Repository(Database()), [1, 2])

    print(tape.tree())

    for caller in tape.roots():
        paths = [child.path for child in tape.children_of(caller)]
        if "__main__:Connection.close" not in paths:
            print("leaked by", caller)
```

```
__main__:Repository.find(table='products', key=1)  -> (1, 'widget')
  __main__:Database.connect()  -> <Connection 1>
  __main__:Connection.close()  -> None
__main__:Repository.find(table='products', key=2)  -> None
  __main__:Database.connect()  -> <Connection 2>
__main__:Repository.count(table='products')  -> 0
  __main__:Database.connect()  -> <Connection 3>
  __main__:Connection.close()  -> None
leaked by __main__:Repository.find(table='products', key=2)
```

The tree shows the bug as it happened. `find()` with a key that matched released its connection, `find()` with a key that did not match never called `close()`, and `count()` released on the way out of its `finally`.

When the method is long, or acquires in several places, you want the line rather than the method. Stack capture on the acquire binding records the calling frame with each event, priced per binding so only the acquire pays for it:

```python
connect = wrapture.binding(Database, "connect", stack="caller")

with wrapture.timeline(connect, close):
    report(Repository(Database()), [1, 2])

    released = {event.instance for event in close.events}
    for event in connect.events:
        if event.result not in released:
            frame = wrapture.stack_frames(event.stack)[0]
            print(f"{event.result} acquired at line {frame.lineno} in {frame.function}, never released")
```

```
<Connection 2> acquired at line 40 in Repository.find, never released
```

## Order across bindings

Per-binding logs answer questions about one call site; the tape answers questions about the flow between them. `tape.assert_order(connect, close)` is a subsequence check across any bindings: other events may appear before, between and after, and only the relative order of the named bindings' events matters. A step can also be a filtered log, which is how to say which call, so `tape.assert_order(charge.events.raising(TimeoutError), refund)` reads as "the refund came after the charge that timed out". `consecutive=True` requires the steps to match a consecutive run with nothing of those bindings' in between, and `exact=True` requires those bindings' events to be exactly the steps, which are mock's `assert_has_calls` and `mock_calls ==` respectively, except that they work across bindings instead of within one mock.

On failure the message names where the walk stalled and prints the actual timeline, which reads far better than a list diff. Asserting a close before a connect on a run that only leaked:

```
AssertionError: expected order not satisfied; stalled waiting for __main__:Database.connect (position 2 of 2)
  actual timeline:
    __main__:Repository.find(table='products', key=2)
    __main__:Database.connect()
    __main__:Repository.count(table='products')
    __main__:Database.connect()
    __main__:Connection.close()
```

## Scoping instead of resetting

A tape is never cleared. Where a mock suite reaches for `reset_mock()` to discard setup calls before the act step, wrapture opens the timeline around the part that counts. Timelines nest, and an inner `timeline()` with no arguments records only what happens inside it while the outer one keeps the whole run:

```python
with wrapture.timeline(connect, close) as whole:
    repository = Repository(Database())
    repository.count("products")                # lands on `whole` only

    with wrapture.timeline() as act:
        repository.find("products", 1)
        connect.events.assert_once()            # the act step alone
```

Inside the inner block `connect.events` reads the innermost tape, so the count is one even though the outer tape holds four events. The same scoping is how a phased test keeps each phase's counts separate, one timeline per phase, with the same bindings applied on entry and removed on exit each time. The second phase can then state `assert_never()` outright, where one cumulative tape could only say the count is still one.

## Messages and phases as events

Calls are not the only thing that records. An attribute binding records reads and writes of an attribute as `get` and `set` events on the same tape, which for this example means the `closed` flag can be watched directly rather than inferred from `close()` being called. That is a subject for a later post. Two other event producers are worth knowing about now, because they change what a test can pin an assertion to.

The first is log capture. `capture_logs()` records standard library logging onto the tape as events of kind `"log"`, selected by logger name pattern and level, and it applies like a binding so `timeline()` accepts it alongside them. Give the repository a warning when nothing is found, and the message lands inside the call that logged it:

```python
logs = wrapture.capture_logs("myapp.*")

with wrapture.timeline(find, connect, close, logs) as tape:
    report(Repository(Database()), [1, 2])

    print(tape.tree())

    warning = logs.events.at_level("WARNING").with_message("*no row*").assert_once().first
    assert tape.parent_of(warning) is find.events.with_args(key=2).first
```

```
__main__:Repository.find(table='products', key=1)  -> (1, 'widget')
  __main__:Database.connect()  -> <Connection 1>
  __main__:Connection.close()  -> None
__main__:Repository.find(table='products', key=2)  -> None
  __main__:Database.connect()  -> <Connection 2>
  log myapp.repo WARNING 'no row in products with id 2'
__main__:Database.connect()  -> <Connection 3>
__main__:Connection.close()  -> None
```

That last assertion is the one pytest's `caplog` has no words for: the warning was logged by this call, not merely somewhere during the test. Capture sits at `Logger.handle`, so it hears each record once on the logger that emitted it, before propagation and regardless of handler configuration, and nothing the application configured is touched.

The second is a block. `wrapture.block(name)` is a context manager the code, or the test, uses to declare a stretch of code as one event, with everything recorded inside it nested underneath. In a test body it names the phases of an integration test so that "the events during the second request" stops being an exercise in parent-chasing:

```python
with wrapture.timeline(connect, close) as tape:
    repository = Repository(Database())

    with wrapture.block("lookups"):
        repository.find("products", 1)
        repository.find("products", 2)

    with wrapture.block("summary"):
        repository.count("products")

    lookups = tape.blocks("lookups").assert_once().first
    tape.within(lookups).for_binding(close).assert_once()
```

```
block: lookups
  __main__:Database.connect()  -> <Connection 1>
  __main__:Connection.close()  -> None
  __main__:Database.connect()  -> <Connection 2>
block: summary
  __main__:Database.connect()  -> <Connection 3>
  __main__:Connection.close()  -> None
```

`tape.within(event)` scopes the whole query surface to one block's contents, so an ordering assertion on the view never sees an event outside it. In application code the same marker is inert when nothing is listening, so it can stay in production code permanently, which is what makes the same block a span when the events are going to a tracing backend rather than a test.

## As a pytest test

In a test the pairing becomes the assertion, and the failure message carries the leaked connections and where each was acquired. `close` is given a declared expectation of at least one call, so a path that acquires nothing at all cannot pass by accident:

```python
def test_find_releases_its_connection():
    connect = wrapture.binding(Database, "connect", stack="caller")
    close = wrapture.binding(Connection, "close").expect_at_least(1)

    with wrapture.timeline(connect, close):
        report(Repository(Database()), [1, 2])

        released = {event.instance for event in close.events}
        leaked = [
            (event.result, wrapture.stack_frames(event.stack)[0])
            for event in connect.events
            if event.result not in released
        ]

        assert not leaked, f"connections left open: {leaked}"
```

The test fails today, naming `<Connection 2>` and the frame inside `find()`. Fix the early return with a `finally` and it passes. With the pytest plugin enabled the tape's tree is attached to the failure report as well, so the output shows what ran rather than only the assertion that tripped.

## What's next

Everything in this post recorded real calls with the bindings doing nothing but watch. The next post is about the other direction, changing what a call does, and specifically about behaviour that changes over time as the code under test keeps calling, which is what retry logic and circuit breakers need from a test.
