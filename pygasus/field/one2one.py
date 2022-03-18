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

"""A one-to-one relationship as a Pygasus field."""

from typing import Any, TYPE_CHECKING

from pydantic.main import ModelField

from pygasus.field.base import PygasusField

if TYPE_CHECKING:
    from pygasus.model.base import Model  # pragma: no cover
    from pygasus.storage.abc import AbstractStorageEngine  # pragma: no cover


class One2OneField(PygasusField):

    """One-to-one field, wrapping around a Pydantic ModelField."""

    def __init__(self, field: ModelField):
        self.__field__ = field
        self.__model__ = None
        self.__storage__ = None
        self.__required__ = ...
        self.__back__ = ...

    def bind(self, model: "Model", storage: "AbstractStorageEngine"):
        """Bind this field to the model and storage engine."""
        field = self.__field__
        self.__model__ = model
        self.__storage__ = storage
        self.__required__ = field.required
        back = storage.get_back_field(model, field, field.type_)
        self.__back__ = getattr(field.type_, back.name)

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
        if new_value is None and self.required:
            raise ValueError(
                f"this operation would set the field {self.name} to "
                f"None on {model}, which would break model consistency."
            )

        back = self.__back__
        old = getattr(model, self.name, None)
        if old and back.required:
            raise ValueError(
                f"this operation would set the field {back.name} to "
                f"None on {old}, which would break model consistency."
            )

        # If the new value had a set field before, cancel the change.
        new_back = getattr(new_value, back.name, None)
        if (
            new_value
            and new_back
            and self.required
            and new_back is not new_value
        ):
            raise ValueError(
                f"this operation would set the field {back.name} to "
                f"None on {new_back}, which would break model consistency."
            )

    def perform_update(self, model: "Model", old_value: Any, new_value: Any):
        """Update and propagate the update of this field.

        This method is used to propagate updates to linked fields,
        for instance, the value of updated linked fields through relations.

        Args:
            model (Model): the model object to be updated.
            old_value (Any): the old value.
            new_value (Any): the new value already set in the model.

        """
        back = self.__back__
        if old_value:
            old_value._exists = False
            setattr(old_value, back.name, None)
            old_value._exists = True

        old_back = getattr(getattr(model, self.name, None), back.name, None)
        if old_back:
            old_back._exists = False
            setattr(old_back, self.name, None)
            old_back._exists = True

        # Bind the new value.
        if new_value:
            # Modify this side of the relationship.
            model._exists = False
            setattr(model, self.name, new_value)
            model._exists = True

            # Modify the other side of the relationship.
            new_value._exists = False
            setattr(new_value, back.name, model)
            new_value._exists = True

    def validate_delete(self, model: "Model"):
        """Validate whether deleting this field is possible.

        This method should raise an appropriate exception
        if the deletion isn't allowed for any reason.

        Args:
            model (Model): the model object to be updated.

        """
        back = self.__back__
        back_obj = getattr(model, self.name, None)
        if back.required:
            raise ValueError(
                f"cannot delete {model}.{self.name}, since it would "
                f"set {back_obj}.{back.name} to None, while this "
                "field is mandatory"
            )

    def perform_delete(self, model: "Model"):
        """Delete and propagate if necessary.

        This method is used to propagate deletions to linked fields,
        for instance, the value of deleted linked fields through relations.

        Args:
            model (Model): the model object to be updated.

        """
        back = self.__back__
        back_obj = getattr(model, self.name, None)
        if back_obj:
            back_obj._exists = False
            setattr(back_obj, back.name, None)
            back_obj._exists = True
