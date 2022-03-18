# Copyright (c) 2022, LE GOFF Vincent
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

"""Field dynamic decorator to wrap pydantic.ModelField."""

from typing import Any, TYPE_CHECKING

from pydantic.main import ModelField

if TYPE_CHECKING:
    from pygasus.model.base import Model  # pragma: no cover
    from pygasus.storage.abc import AbstractStorageEngine  # pragma: no cover


class PygasusField:

    """Pygasus field, wrapping around a Pydantic ModelField."""

    def __init__(self, field: ModelField):
        self.__field__ = field
        self.__model__ = None
        self.__storage__ = None

    def __getattr__(self, key):
        if key.startswith("__") and key.endswith("__"):
            raise AttributeError(
                f"class {type(self).__name__} has no attribute {key!r}"
            )
        return getattr(self.__field__, key)

    def __eq__(self, other):
        return self.__storage__.query_builder.eq(self, other)

    def __ne__(self, other):
        return self.__storage__.query_builder.ne(self, other)

    def __lt__(self, other):
        return self.__storage__.query_builder.lt(self, other)

    def __le__(self, other):
        return self.__storage__.query_builder.le(self, other)

    def __gt__(self, other):
        return self.__storage__.query_builder.gt(self, other)

    def __ge__(self, other):
        return self.__storage__.query_builder.ge(self, other)

    def is_in(self, collection):
        """Return models with the field in this collection."""
        return self.__storage__.query_builder.is_in(self, collection)

    def is_not_in(self, collection):
        """Return models with the field not in this collection."""
        return self.__storage__.query_builder.is_not_in(self, collection)

    def has(self, value):
        """Return models with the field having this value (flag)."""
        return self.__storage__.query_builder.has(self, value)

    def has_not(self, value):
        """Return models without the field having this value (flag)."""
        return self.__storage__.query_builder.has_not(self, value)

    # Methods that can be overridden by subclasses.
    def bind(self, model: "Model", storage: "AbstractStorageEngine"):
        """Bind this field to the model and storage engine."""
        self.__model__ = model
        self.__storage__ = storage

    def validate_update(self, model: "Model", old_value: Any, new_value: Any):
        """Validate whether updating this field is possible.

        This method should raise an appropriate exception
        if the update isn't allowed for any reason.

        Args:
            model (Model): the model object to be updated.
            old_value (Any): the old value.
            new_value (Any): the new value which will be applied
                    if this method doesn't raise any exception.

        """

    def perform_update(self, model: "Model", old_value: Any, new_value: Any):
        """Update and propagate the update of this field.

        This method is used to propagate updates to linked fields,
        for instance, the value of updated linked fields through relations.

        Args:
            model (Model): the model object to be updated.
            old_value (Any): the old value.
            new_value (Any): the new value already set in the model.

        """

    def validate_delete(self, model: "Model"):
        """Validate whether deleting this field is possible.

        This method should raise an appropriate exception
        if the deletion isn't allowed for any reason.

        Args:
            model (Model): the model object to be updated.

        """

    def perform_delete(self, model: "Model"):
        """Delete and propagate if necessary.

        This method is used to propagate deletions to linked fields,
        for instance, the value of deleted linked fields through relations.

        Args:
            model (Model): the model object to be updated.

        """
