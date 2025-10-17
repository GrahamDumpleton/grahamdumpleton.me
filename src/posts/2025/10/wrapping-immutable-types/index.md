---
title: "Wrapping immutable objects"
description: "Using the wrapt object proxy around immutable objects."
date: 2025-10-17
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt"]
draft: false
---

I am finally close to releasing `wrapt` version 2.0.0. The release has been delayed a bit as someone raised a number of questions about special Python dunder methods which the `ObjectProxy` class in `wrapt` didn't support.

Some of these were omissions due to the fact that the special methods did not exist when `wrapt` was first implemented, nor were they a part of initial Python 3 versions when support was added for Python 3. In particular, the `__matmul__`, `__rmatmul__` and `__imatmul__` dunder methods which underly the matrix multiplication operators added in Python 3.5. In other cases that no default support for specific dunder methods existed was a more complicated situation.

I am not going to dwell on the latter in this post, but as part of the overall discussion with the person who raised the questions, they also pointed out some issues with how the dunder methods for in-place operators were handled in the `ObjectProxy` class, which is going to be the subject of this post, as it may be an interesting technical exploration.

An in-place operator in Python is an operator that modifies a variable directly without creating a new object. It combines an operation with assignment.

In Python, in-place operators include:

* `+=` (add and assign)
* `-=` (subtract and assign)
* `*=` (multiply and assign)
* `/=` (divide and assign)
* `//=` (floor divide and assign)
* `%=` (modulo and assign)
* `**=` (exponentiate and assign)
* `@=` (matrix multiply and assign - Python 3.5+)
* `&=`, `|=`, `^=` (bitwise operations and assign)
* `<<=`, `>>=` (bit shift and assign)

Obvious example of using an in-place operator is on integers.

```
value = 1
value += 1
```

The result being that `value` ends up being set to 2.

Other examples are tuples and lists:

```
tuple_values = (1, 2, 3)
tuple_values += (4, 5, 6)

list_values = [1, 2, 3]
list_values += [4, 5, 6]
```

In each of these cases the members of the respective data structures are the integers from 1 to 6.

A potential trap for programmers new to Python arises when combining variable aliasing and in-place operators.

```
tuple_values_1 = (1, 2, 3)
tuple_values_2 = tuple_values_1

tuple_values_2 += (4, 5, 6)

list_values_1 = [1, 2, 3]
list_values_2 = list_values_1

list_values_2 += [4, 5, 6]
```

For the case of the tuples, `tuple_values_1` ends up as `(1, 2, 3)` and `tuple_values_2` as `(1, 2, 3, 4, 5, 6)`.

For the lists however, both `list_values_1` and `list_values_2` end up being set to `[1, 2, 3, 4, 5, 6]`.

The reason for this is that although both variables for the tuple and list in each case initially point to the same object, the alias or reference is broken in the case of the tuple when the in-place operator is applied to it. This occurs because the instance of a tuple is an immutable where as an instance of a list can be modified.

In practice what this means is that although you use the `+=` operator, for an immutable type such as tuple, it will be implemented under the covers as:

```
tuple_values_2 = tuple_values_2 + (4, 5, 6)
```

In other words, the variable which prior to that point had been an alias for the original tuple, is replaced with a new object which is the result of adding the extra member items to the tuple.

Although this highlights the problem of using in-place operators when using aliasing, there is actually a more insidious case where this can present itself.

Take for example the case of a class definition with attributes declared at class scope, where we then create an instance of the class, and apply the in-place operator to the attributes of the class via the instance.

```
class Class:
    tuple_values = (1, 2, 3)
    list_values = [1, 2, 3]

c = Class()

c.tuple_values += (4, 5, 6)
c.list_values += [4, 5, 6]
```

Without knowing better, you might think that the result will be that `Class.tuple_values` ends up being set to `(1, 2, 3, 4, 5, 6)` and that `Class.list_values` will be similarly set to `[1, 2, 3, 4, 5, 6]`. For the case of the tuple this isn't actually what happens.

Although `Class.list_values` does end up being set to `[1, 2, 3, 4, 5, 6]`, the value of `Class.tuple_values` remains as `(1, 2, 3)`.

The reason for this is that since the tuple is immutable, as mentioned above, it will actually effectively be implemented under the covers as:

```
c.tuple_values = c.tuple_values + (4, 5, 6)
```

And this is where the potentially non obvious happens.

To explain, think now that if instead of accessing the attribute via the instance of the class, you had accessed the class directly.

```
C.tuple_values += (4, 5, 6)
```

As already noted, this would have been implemented as:

```
C.tuple_values = C.tuple_values + (4, 5, 6)
```

It is obvious then that the change would be applied to the class scoped attribute and `C.tuple_values` would be `(1, 2, 3, 4, 5, 6)`.

Look again now at what happened though when accessing the attribute via the instance of the class.

```
c.tuple_values = c.tuple_values + (4, 5, 6)
```

Because tuple is immutable, the existing values of the attribute is first read. At this point though, the instance of the class doesn't actually have an attribute `tuple_values`, so what happens is that it falls back to reading from the class scoped attribute of the same name.

The value `(4, 5, 6)` is added to the value read from the class scoped attribute, and the result assigned back to the attribute. In doing the assignment though, since it was accessed via the class instance, instead of updating the class scoped attribute, it results in the creation of a new attribute against that instance of the class.

To explain it another way, prior to updating the attribute, if we had done:

```
print(vars(c))
```

the result would have been an empty dictionary, showing that the instance had no attributes, but after updating `tuple_values` we see:

```
{'tuple_values': (1, 2, 3, 4, 5, 6)}
```

indicating that the instance now had a separate attribute to that defined on the class.

Just to complicate things even more, if you look at the attributes of the instance after updating `list_values` you will also see it defined on the instance as well. For it though, since a list is mutable, it is still an alias to the same list object defined as a class attribute. Confused yet?

This is because although I said that for an immutable type it gets implemented under the covers as:

```
c.tuple_values = c.tuple_values + (4, 5, 6)
```

this isn't quite true.

It is closer to say that what occurs is:

```
if "tuple_values" not in vars(c):
    tmp = C.tuple_values
else:
    tmp = c.tuple_values

tmp += (4, 5, 6)

c.tuple_values = tmp
```

but where because tuple is immutable, ends up being:

```
if "tuple_values" not in vars(c):
    tmp = C.tuple_values
else:
    tmp = c.tuple_values

tmp = tmp + (4, 5, 6)

c.tuple_values = tmp
```

For the case of the list, it is similarly implemented as:

```
if "list_values" not in vars(c):
    tmp = C.list_values
else:
    tmp = c.list_values

tmp += [4, 5, 6]

c.list_values = tmp
```

but since a list is mutable, it can be modified in place, meaning that since both the attribute on the instance and the class refer to the same list object, the change is seen when accessed via either.

There is no doubt I have explained this very badly, but if I haven't lost you, you might be thinking now what has this all got to do with using the `ObjectProxy` class in `wrapt`.

I am not going to go into details how one uses `wrapt` to monkey patch code, and I also question why anyone would try and wrap an instance of an immutable type in the first place, but the original problem that was raised boils down to the following code when using `ObjectProxy` in `wrapt`:

```
class Class:
    tuple_values = wrapt.ObjectProxy((1, 2, 3))

c = Class()

c.tuple_values += (4, 5, 6)
```

The point of `ObjectProxy` is that it acts as a transparent proxy for a wrapped object, where operations on the proxy object should end up with the same result as if the original object was used and it was not wrapped by the proxy.

If this was true, then we should expect that after the above code had executed, `Class.tuple_values` when accessed should have resulted in `(1, 2, 3)` and `c.tuple_values` would be `(1, 2, 3, 4, 5, 6)`.

The problem is that this was not what was happening and instead the effective value was in both cases `(1, 2, 3, 4, 5, 6)`.

In other words `wrapt` was breaking the rules of what should happen for an immutable type.

The first reason for this is that the `ObjectProxy` instance that replaces (wraps) the original mutable object is now a rather complicated class instance.

In order to handle the in-place operator for addition being applied to the proxy, the `ObjectProxy` class needs to implement the special dunder method `__iadd__`. When we say:

```
c.tuple_values += (4, 5, 6)
```

this gets translated into:

```
c.tuple_values = c.__iadd__((4, 5, 6))
```

In order to have the operation be applied to the wrapped object, the `__iadd__` method of `ObjectProxy` was implemented as:

```
    def __iadd__(self, other):
        self.__wrapped__ += other
        return self
```

On face value this may seem to be correct, but fails for the case of an immutable object.

Going back to what we said occurs under the covers when we use `+=` we now have:

```
if "tuple_values" not in vars(c):
    tmp = C.tuple_values
else:
    tmp = c.tuple_values

tmp = tmp.__iadd__((4, 5, 6))

c.tuple_values = tmp
```

The original wrapped object at this point exists as the `__wrapped__` attribute on the `ObjectProxy` instance referenced by the temporary value.

When `+=` is executed, that calls `__iadd__` which results in:

```
        self.__wrapped__ += other
```

which as have explained, since the wrapped object is immutable is implemented as:

```
        self.__wrapped__ = self.__wrapped__ + other
```

Since though both the attribute on the instance, and the class, reference the same proxy object, and although we are replacing the tuple with the updated value, that is only occuring against the `__wrapped__` attribute of the `ObjectProxy` instance itself.

What is meant to happen in order to be able to replace the original attribute reference, is that `__iadd__` should return any new object to replace it, but as the code was written, it was always returning `self`. Thus, the original proxy object is what gets set as the attribute on the instance as the temporary value reference doesn't change.

As much as this is an obscure corner case which in practice would probably never arise since wrapping immutable objects is a questionable use case, the question now is how to fix this and do something different when an immutable object is being wrapped.

Although Python has various builtin immutable types, there isn't a single test one can run to determine if an object is immutable. What we can do though for our specific case of the `__iadd__` method implementation, is to assume that if the wrapped object does not itself implement `__iadd__` that it is immutable for the purposes of that operation.

The simplistic approach for an immutable object would then be to discard the fact that an `ObjectProxy` wrapper was being used, and return the result of adding the wrapped object with the argument to `+=`.

```
    def __iadd__(self, other):
        if hasattr(self.__wrapped__, "__iadd__"):
            self.__wrapped__ += other
            return self
        else:
            return self.__wrapped__ + other
```

This isn't a good solution though as there is going to be some reason `ObjectProxy` was used in the first place, and we have just thrown it away, with any custom behaviour the proxy object implemented lost.

The next alternative is to return the result of using addition within a new instance of `ObjectProxy`.

```
    def __iadd__(self, other):
        if hasattr(self.__wrapped__, "__iadd__"):
            self.__wrapped__ += other
            return self
        else:
            return ObjectProxy(self.__wrapped__ + other)
```

Because though any custom behaviour of an object proxy is going to be implemented by a class derived from `ObjectProxy`, we again are changing the expected overall behaviour of the proxy object, as only the `ObjectProxy` base class behaviour is preserved.

Python being a dynamic programming language with introspection capabilities builtin does mean though that we can work out what class type was used to create the proxy object in the first place. We could therefore instead use:

```
    def __iadd__(self, other):
        if hasattr(self.__wrapped__, "__iadd__"):
            self.__wrapped__ += other
            return self
        else:
            return type(self)(self.__wrapped__ + other)
```

Unfortunately though, this can also fail.

The problem now is that a custom object proxy type derived from `ObjectProxy` could override `__init__()` such that instead of it taking a single argument which is the object to be wrapped, takes one or more distinct arguments which are used in the creation of the wrapped object. If this is the case creation of the new proxy object could fail due to mismatched number of arguments or what the argument means.

A further issue is that a custom object proxy could maintain additional state within the custom object proxy which because it isn't transferred into the new proxy object would be lost.

To cut to the solution, what can be done is for `ObjectProxy` to be implemented as:

```
class ObjectProxy:
    ...

    @property
    def __object_proxy__(self):
        return ObjectProxy

    def __iadd__(self, other):
        if hasattr(self.__wrapped__, "__iadd__"):
            self.__wrapped__ += other
            return self
        else:
            return self.__object_proxy__(self.__wrapped__ + other)
```

That is, we add a property `__object_proxy__` to `ObjectProxy` which returns a callable (by default `ObjectProxy`) which can be used to create a new instance of the proxy object for the modified wrapped object.

The reason for this convoluted approach is that although it is likely going to be a rare situation, it does allow for a custom object proxy to override how a new proxy object is created.

```
class CustomObjectProxy(ObjectProxy):
    def __init__(self, arg1, arg2, *, wrapped=None):
        ```The arg1 and arg2 values are inputs to originally create
        object to be wrapped. If wrapped is not None, then we adopt
        that as wrapped object but still record inputs for later use.
        ```

        self._self_arg1 = arg1
        self._self_arg2 = arg2

        # Create object to be wrapped based on inputs.

        wrapped = ...

        super().__init__(wrapped)

    @property
    def __object_proxy__(self):
        def __ctor__(wrapped):
            # We need to override what __init__() does so construct
            # class using more manual steps.

            instance = ObjectProxy.__new__(CustomObjectProxy)

            instance._self_arg1 = self._self_arg1
            instance._self_arg2 = self._self_arg2

            ObjectProxy.__init__(instance, wrapped)

            return instance

        return __ctor__
```

One caveat on having the `__object_proxy__` property return `ObjectProxy` by default is that even if a custom object proxy type still accepts the wrapped object directly when being initialized, it would need to override `__object_proxy__` to return the custom object proxy type, if it is ever intended to be used to wrap immutable objects.

The alternative is to define `ObjectProxy` as:

```
class ObjectProxy:
    ...

    @property
    def __object_proxy__(self):
        return type(self)
```

This means it will work out of the box for custom object proxy which are initialized with the object to be wrapped, but then you will have the problem mentioned before where a derived class has a custom `__init__()` function which takes different arguments.

Either way, if not overridden, you will get a silent failure resulting in different behaviour after an in-place operator is used, or for the case of custom arguments to `__init__()`, an outright exception.

For now at least opting to return `ObjectProxy` rather than the type of a derived custom object proxy. Someone would already need to be doing something crazy to need to wrap immutable types and so is highly unlikely to encounter the whole issue anyway. Thus returning `ObjectProxy` seems to be the slightly safer choice.

Having a solution, we now just need to update all the other in-place operators with similar pattern of code. For example, in-place multiplication.

```
    def __imul__(self, other):
        if hasattr(self.__wrapped__, "__imul__"):
            self.__wrapped__ *= other
            return self
        else:
            return self.__object_proxy__(self.__wrapped__ * other)
```

Or at least we are done for the pure Python implementation. Since `wrapt` actually uses a C extension and only falls back to the pure Python implementation if the C extension is not available for some reason, all this also had to be done for the C extension as well. How it is done in the C extension will be left to the readers imagination.

End result is that although I have never had anyone report this as a real world problem, and it was only reported as technically wrong, it will be addressed in `wrapt` version 2.0.0 as discussed above. Since have not seen it as a problem in the real world, I will not be back porting it to version 1.17.X.

Anyway, hope this was an interesting exploration of a strange corner case.
