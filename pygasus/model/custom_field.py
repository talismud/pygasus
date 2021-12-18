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

"""Custom field class, to add field support to Pygasus."""

from abc import ABCMeta, abstractmethod
from typing import Any


class CustomField(metaclass=ABCMeta):

    """Abstract class to define a custom field.

    Custom fields should inherit from this class and redefine some
    attributes and methods.  A custom field provides a way
    to store custom information on a model beyond supported fields.

    Attributes to override:
        field_name (str): the field name, a reference.

    Methods to override:
        init(): initializes the field.  This method is called
                when the field is added to a storage engine
                (before it is applied to individual models).
        add(model, field): method called when the custom field
                is added to a model.  The type of the field as supported
                by the storage engine (like `bytes`) should be returned
                at this point, in order for the storage engine
                to know how to store this field.

    """

    def __init__(self, storage_engine, model, field):
        self.storage_engine = storage_engine
        self.model = model
        self.field = field
        self.options = {}

    @abstractmethod
    def add(self) -> Any:
        """Add this field to a model.

        Returns:
            annotation type (Any): the type of field to store.

        """

    @abstractmethod
    def to_storage(self, value: Any) -> Any:
        """Return the value to store in the storage engine.

        Args:
            value (Any): the original value in the field.

        Returns:
            to_store (Any): the value to store.
            It must be of the same type as returned by `add`.

        """

    @abstractmethod
    def to_field(self, value: Any) -> Any:
        """Convert the stored value to the field value.

        Args:
            value (Any): the stored value (same type as returned by `add`).

        Returns:
            to_field (Any): the value to store in the field.
            It must be of the same type as the annotation hint used
            in the model.

        """
