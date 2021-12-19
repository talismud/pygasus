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

"""Abstract query builder.

The query builder is responsible for connecting generic, Pygasus
queries with the selected storage engine.  For instance, when
comparing a field against a value:

```
>>> User.id == 5
<...>
>>>
```

The selected `StorageEngine`, the one that has bound this model,
will return a valid comparator used in queries.  This will speed
up treatment and avoid generic to concrete conversion on the fly.

"""

from abc import ABCMeta, abstractmethod


class AbstractQueryBuilder(metaclass=ABCMeta):

    """Abstract query builder.

    This class is responsible for connecting generic queries
    to the storage engine.  Several methods are provided as abstract.

    Abstract methods:
        eq: provide == comparison.

    """

    def __init__(self, storage_engine):
        self.storage_engine = storage_engine

    @abstractmethod
    def eq(self, field, other):
        """Compare field to other."""

    @abstractmethod
    def ne(self, field, other):
        """Compare field to other."""

    @abstractmethod
    def lt(self, field, other):
        """Compare field to other."""

    @abstractmethod
    def le(self, field, other):
        """Compare field to other."""

    @abstractmethod
    def gt(self, field, other):
        """Compare field to other."""

    @abstractmethod
    def ge(self, field, other):
        """Compare field to other."""

    @abstractmethod
    def is_in(self, field, collection):
        """Filter fields with a value in a collection."""

    @abstractmethod
    def is_not_in(self, field, collection):
        """Filter fields with a value not in a collection."""

    @abstractmethod
    def has(self, field, value):
        """Return models with the field having this value (flag)."""

    @abstractmethod
    def has_not(self, field, collection):
        """Return models without the field having this value (flag)."""
