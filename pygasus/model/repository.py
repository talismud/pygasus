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

"""Base class for repositories."""


class Repository:

    storage_engine = None

    def __init__(self, model):
        self.model = model

    def create(self, **data):
        """Create an object.

        Object fields are transmitted as keyword arguments.
        The field must build a complete model object which
        will be validated before a row is written to the
        database.  However, keyword arguments that
        contain information provided by the database
        (such as autoincrement) aren't to be specified.

        Args:
            Keyword arguments to send to the model.

        Example:

            account = repository.create(username="me",
                hashed_password=b"something", ...)

        """
        return self.storage_engine.insert(self.model, data)

    def insert_at(self, *args, **data):
        """Create an object at a given index.

        Object fields are transmitted as keyword arguments.
        The field must build a complete model object which
        will be validated before a row is written to the
        database.  However, keyword arguments that
        contain information provided by the database
        (such as autoincrement) aren't to be specified.

        Args:
            index (int): the index at which to place this model.
            Keyword arguments to send to the model.

        """
        index = args[0]
        return self.storage_engine.insert_at(self.model, data, index)

    def select(self, query):
        """Retrieve model instances based on a query.

        Args:
            The data to be sent to the database.
            query: the query to filter models.

        Examle:
            account = repository.select(Account.username == "me")

        """
        return self.storage_engine.select(self.model, query)

    def get(self, **data):
        """Retrieve a model instance.

        Keyword arguments are used to specify one or more fields
        to identify the object in the database.  Usually,
        these fields are primary keys or unique fields.

        Args:
            The data to be sent to the database.

        Examle :
            account = repository.get(id=5)

        """
        return self.storage_engine.get(self.model, **data)

    def update(self, instance, key, old_value, new_value):
        """Inform of an update."""
        self.storage_engine.update(
            self.model,
            instance,
            key,
            old_value,
            new_value,
        )

    def delete(self, instance):
        """Delete the specified instance.

        This method will remove the instance from the cache as well.

        Args:
            instance (Model): a model instance.

        """
        self.storage_engine.delete(self.model, instance)

    def bulk_delete(self, query) -> int:
        """Delete model instances based on a query.

        Args:
            query: the query to filter models.

        Examle:
            account = repository.bulk_delete(Account.username == "me")

        """
        return self.storage_engine.bulk_delete(self.model, query)
