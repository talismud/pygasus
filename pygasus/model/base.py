# Copyright (c) 2021, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Base Model for all Pygasus stored objects.

All data models destined to be stored in Pygasus should inherit,
directly or indirectly, from the `Model` class defined here.
Models are described using simple type annotation
and inherit from Pydantic `BaseModel`, so they share the features
of models defined in Pydantic.

```python
from typing import Optional

grom pygasus import Model

class User(Model):

    '''A User model.'''

    id: int
    name: str
    age: int
    gender: Optional[str]
```

Behind the scenes, a Pygasus model is meant to be light and mostly
independent from the storage utility.  It is linked to a repository,
which is defined bvy default (but you can easily override it).
This repository has access to the storage utility and can perform
more advanced queries.  For convenience's sake, the `__setattr__` method
of models is linked to the UPDATE operation on the repository, so that
modifying a model will update it in storage as well.  This is the only
convenience (creating a model as usual with `__init__` won't do
anything in regard to the storage).  Of course, you can still access
the repository and perform these operations:

```python
# This will perform an INSERT operation on the user repository.
new_user = User.repository.create(name="Vincent", age=33)
# At this point, the new user has an ID which is set by the storage utility.
print(new_user.id)
# And this will perform an UPDATE operation.
new_user.age = 21
# This will fetch the user with id of 5.
user_5 = User.repository.get(id=5)
```

"""

from importlib import import_module
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr  # noqa: F401
from pydantic.main import ModelMetaclass

from pygasus.field.base import PygasusField
from pygasus.model.collections import Sequence
from pygasus.model.decorators import LazyPropertyDescriptor, lazy_property
from pygasus.model.helpers import get_primary_keys
from pygasus.model.repository import Repository

MODELS = set()


class MetaModel(ModelMetaclass):

    """Metaclass for all models."""

    def __new__(cls, name, bases, attrs):
        cls = super().__new__(cls, name, bases, attrs)
        cls.__pygasus__ = {}
        if cls.__name__ != "Model":
            MODELS.add(cls)

            # Wrap fields.
            for name, field in cls.__fields__.items():
                pygasus_field = PygasusField(field)
                cls.__pygasus__[name] = pygasus_field
                setattr(cls, name, pygasus_field)
        return cls

    @property
    def repository_path(cls):
        """Return the path leading to the repository, if any."""
        path = cls.__config__.repository_path
        if path is not None:
            return path

        return path

    @lazy_property
    def repository(cls) -> Optional[Repository]:
        """Return the repository object."""
        return load_repository(cls.repository_path, cls)


class Model(BaseModel, metaclass=MetaModel):

    """Abstract class for all models."""

    _exists = PrivateAttr()

    class Config:
        extra = "forbid"
        keep_untouched = (LazyPropertyDescriptor,)
        repository_path = None
        unique = ()
        copy_on_model_validation = False
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        self._exists = False
        super().__init__(**kwargs)
        self._exists = True

    def __getattribute__(self, attr: str) -> Any:
        """Get the attribute doing a storage query if necessary."""
        value = object.__getattribute__(self, attr)
        if attr.startswith("_") or not self._exists:
            return value

        field = self.__fields__.get(attr)
        if field is not None:
            o_type = field.outer_type_
            f_type = field.type_
            if (
                isinstance(f_type, type)
                and issubclass(f_type, Model)
                and o_type is Sequence[f_type]
            ):
                # This object has several related, query the storage if needed.
                value.load_from_storage()
        return value

    def __repr_args__(self):
        args = dict(self.__dict__)
        for key, value in args.items():
            if isinstance(value, Model):
                pkeys = get_primary_keys(value)
                args[key] = str(pkeys)

        return args.items()

    def __setattr__(self, key: str, value: Any):
        """Force an UPDATE operation on the storage."""
        old_value = getattr(self, key, ...)
        exists = getattr(self, "_exists", False)
        cls_attr = getattr(type(self), key, None)
        if isinstance(cls_attr, (property, LazyPropertyDescriptor)):
            object.__setattr__(self, key, value)
            return

        if exists and not key.startswith("_"):
            # Inform the repositories of a change.
            repository = type(self).repository
            if repository:
                repository.update(self, key, old_value, value)
        super().__setattr__(key, value)

    def __eq__(self, other):
        """Don't compare dict like Pydantic does, just compare field values."""
        if not isinstance(other, type(self)):
            return False

        common = True
        for name, field in self.__fields__.items():
            value1 = getattr(self, name, ...)
            value2 = getattr(other, name, ...)
            if isinstance(value1, Model) or isinstance(value2, Model):
                common = get_primary_keys(
                    value1, include_model_name=True
                ) == get_primary_keys(value2, include_model_name=True)
            elif value1 != value2:
                common = False

            if not common:
                break

        return common


def load_repository(path: str, model: Type[Model]) -> Repository:
    """Try to load and return the repository."""
    if path is None:
        return Repository(model)

    module = import_module(path)

    # Look into the path, there may not be more than one class,
    # this is the repository.
    repository_cls = None
    for name, value in module.__dict__.items():
        if name.startswith("_"):
            continue

        if isinstance(value, type) and issubclass(value, Repository):
            if value.__module__ != path:
                continue

            if repository_cls is not None:
                repository_cls = ...
                break
            else:
                repository_cls = value

    if repository_cls is None:
        raise ValueError(f"No repository could be found in {path}.")
    elif repository_cls is ...:
        raise ValueError(
            "More than one repository are present "
            f"in module {path}, not loading any."
        )
    else:
        return repository_cls(model)
