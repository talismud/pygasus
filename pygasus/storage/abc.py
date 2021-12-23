# Copyright (c) 2021, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of ytranslate nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Module containing the abstract class for storage engines."""

from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional, Set, Type

from pygasus.model import CustomField, Field, Model, Sequence
from pygasus.storage.query_builder import AbstractQueryBuilder


class AbstractStorageEngine(metaclass=ABCMeta):

    """Abstract storage engine.

    The storage engine is here to store, retrieve, create, delete,
    and fetch models from a persistent storage system (like
    a database).  The implementation of such a storage engine
    depends on the storage system being used.

    """

    query_builder: AbstractQueryBuilder = None

    def __init__(self):
        self.models = {}
        self.custom_fields = {}
        self.cache = {}

    def add_custom_field(self, field: Type[CustomField], **kwargs):
        """Add support for a custom field.

        Args:
            field (CustomField): the custom field class.

        Additional keyword arguments can be sent and will be stored
        as options for the custom field.

        """

    def add_custom_field_to_model(
        self,
        custom_field: Type[CustomField],
        model: Model,
        field: Field,
    ) -> CustomField:
        """Add a custom field to a model.

        Args:
            custom_field (CustomField): the custom field to add.
            model (Model): the model to add this field to.
            field (Field): the generic field.

        Returns:
            custom_field (CustomField): the instanciated custom field.

        """
        custom_field = custom_field(self, model, field)
        self.custom_fields[(model, field.name)] = custom_field
        return custom_field.add()

    # Abstract methods
    @abstractmethod
    def init(self):
        """
        Initialize the storage engine.

        Positional and/or keyword arguments can be supported
        in the subclass.  This method is called like a
        "second constructor", where options can be specified and
        connection to the storage engine can be established.
        The connection to the storage engine in particular
        doesn't occur when the object is created, which
        might have side-effects.

        """

    @abstractmethod
    def close(self):
        """Close the connection to the storage engine."""

    @abstractmethod
    def destroy(self):
        """Close and destroy the storage engine."""

    def bind(self, models: Optional[Set[Type[Model]]] = None):
        """Bind the speicifed models to this controller.

        If the models aren't specified, then bind every model found
        in the default set.  This is often desirable, although adding
        every model means that one should only import a class in order
        for it to be present.  TalisMUD has a lt of systems of dynamic
        importing, which can make this choice complicated in some
        instances.

        """
        models = models if models is not None else set()
        names = {model.__name__: model for model in models}
        for model in models:
            model.update_forward_refs(**names)

        for model in models:
            # Generate the model's repository.
            model.repository.storage_engine = self

            # Bind this model to the storage engine.
            self.bind_model(model, names)

    @abstractmethod
    def bind_model(self, model: Type[Model], names: Dict[str, Type[Model]]):
        """Bind this storage engine to a specific model.

        Args:
            model (subclass of Model): the model to bind.
            names (dict): the dictionary (name: model) of other models.

        """

    @abstractmethod
    def insert(self, model: Type[Model], **kwargs):
        """Add a new row for this model.

        The model is used to determine the collection in storage.
        Keyword arguments are used to specify data for this new model.

        Args:
            model (subclass of Model): the model class.
            Additional keyword arguments are expected.

        """

    @abstractmethod
    def get(self, model: Type[Model], **kwargs):
        """Get a model instance with the specified arguments.

        Keyword arguments to this method should hold values for
        primary key(s) of the specified model
        (`id` is a common one).

        Args:
            model (subclass of Model): the model object.

        Keyword arguments should contain primary key(s) value(s)
        or other unique fields.

        Returns:
            instance (Model): the model isntance or None.

        Note:
            This method will raise an exception if more than one
            stored instance matches the specified filters.

        """

    @abstractmethod
    def get_related(self, sequence: Sequence) -> List[Model]:
        """Retrieve the related objects from a collection.

        The collection is a sequence that represents various objects
        related to the parent model.

        Args:
            sequence (Sequence): the collection.

        Returns:
            models (list of Model): the models.

        """

    @abstractmethod
    def update(self, model, instance, key, old_value, new_value):
        """
        Update an instance attribute.

        Args:
            model (subclass of Model): the model class.
            instance (Model: the model object.
            key (str): the name of the attribute to modify.
            old_value (Any): the value before the modification.
            new_value (Any): the value after the modification.

        """

    @abstractmethod
    def delete(self, model: Type[Model], instance: Model):
        """Delete the specified model.

        Args:
            model (subclass of Model): the model class.
            instance (Model): the model instance.

        The model also is removed from cache.

        """

    @abstractmethod
    def bulk_delete(self, model: Type[Model], query) -> int:
        """Select one or more models with the specified query and delete them.

        Args:
            model (subclass of Model): the model object.
            query: the query object by which to filter.

        Returns:
            number (int): the number of deleted rows.

        """

    # Helper methods.
    def get_back_field(self, model, field, left):
        """Return, if found, the bac field of the relationship.

        Args:
            model (subclass of Model): the Model subclass.
            field (Field): the field.
            left (Model): the model linked to the relationship.

        """
        back_name = field.field_info.extra.get("back", "")
        back_fields = (
            {
                b_field
                for b_field in left.__fields__.values()
                if b_field.name == back_name and b_field.type_ is model
            },
            {
                b_field
                for b_field in left.__fields__.values()
                if b_field.type_ is model
            },
        )

        for fields in back_fields:
            if len(fields) == 1:
                return fields.pop()

        # At this point, no unique field was found.
        raise ValueError(
            "no back field could be found for the relationship "
            f"{model.__name__}.{field.name}.  Possible candidates "
            f"are: {fields}.  Perhaps you forgot to add a back reference "
            f"in the {left.__name__} model?"
        )
