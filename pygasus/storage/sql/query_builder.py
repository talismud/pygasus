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

"""SQLAlchemy query builder."""

from pygasus.storage.query_builder import AbstractQueryBuilder


class SQLQueryBuilder(AbstractQueryBuilder):

    """Query builder for SQLAlchemy."""

    def _get_table(self, field):
        """Return the table for this model."""
        model = field.__model__
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        return self.storage_engine.tables[model_name]

    def eq(self, field, other):
        """Compare field to other."""
        table = self._get_table(field)
        return getattr(table.c, field.name) == other

    def ne(self, field, other):
        """Compare field to other."""
        table = self._get_table(field)
        return getattr(table.c, field.name) != other

    def lt(self, field, other):
        """Compare field to other."""
        table = self._get_table(field)
        return getattr(table.c, field.name) < other

    def le(self, field, other):
        """Compare field to other."""
        table = self._get_table(field)
        return getattr(table.c, field.name) <= other

    def gt(self, field, other):
        """Compare field to other."""
        table = self._get_table(field)
        return getattr(table.c, field.name) > other

    def ge(self, field, other):
        """Compare field to other."""
        table = self._get_table(field)
        return getattr(table.c, field.name) >= other

    def is_in(self, field, collection):
        """Filter fields with a value in a collection."""
        table = self._get_table(field)
        return getattr(table.c, field.name).in_(collection)

    def is_not_in(self, field, collection):
        """Filter fields with a value not in a collection."""
        table = self._get_table(field)
        return getattr(table.c, field.name).not_in(collection)

    def has(self, field, value):
        """Return models with the field having this value (flag)."""
        table = self._get_table(field)
        return getattr(table.c, field.name).op("&")(value.value) == value.value

    def has_not(self, field, value):
        """Return models without the field having this value (flag)."""
        table = self._get_table(field)
        return getattr(table.c, field.name).op("&")(value.value) != value.value
