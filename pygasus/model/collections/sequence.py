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

"""Module containing Sequence to host a list (or set) or data (or models)."""

from collections.abc import MutableSequence
from typing import Any, Generic, List, TypeVar

from pydantic import PrivateAttr
from pydantic.generics import GenericModel

model = TypeVar("model")


class Sequence(GenericModel, MutableSequence, Generic[model]):

    """An optionally-sorted sequence of models, behaving like a list.

    Its major role is to behave like a list and to forward modifications
    to the storage system being used.

    """

    models: List[model] = []
    left_model: Any
    right_model: Any
    left_field: Any
    right_field: Any
    parent: Any = None
    _loaded = PrivateAttr()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded = False

    def __getitem__(self, index: int) -> model:
        return self.models[index]

    def __setitem__(self, index: int, value: model) -> None:
        self.models[index] = value

    def __delitem__(self, index: int) -> None:
        del self.models[index]

    def __len__(self) -> int:
        return len(self.models)

    def __repr__(self) -> str:
        return repr(self.models)

    def __str__(self) -> str:
        return str(self.models)

    def __iter__(self):
        return iter(self.models)

    def insert(self, index: int, value: model) -> None:
        self.models.insert(index, value)

    def append_new(self, **kwargs) -> model:
        """Append a new model object to the list.

        Args:
            Only keyword arguments are supported.  They're used to create
            the new model, using the model's repository.

        Returns:
            model (model instance): the appended model.

        """
        kwargs[self.right_field.name] = self.parent
        obj = self.right_model.repository.create(**kwargs)
        self.append(obj)

    def load_from_storage(self):
        """Load the list from the storage system."""
        if self._loaded:
            return

        engine = self.right_model.repository.storage_engine
        self.models[:] = engine.get_related(self)
        self._loaded = True

    class Config:
        underscore_attrs_are_private = True
        copy_on_model_validation = False
