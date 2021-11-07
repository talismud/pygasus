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

"""Field dynamic decorator to wrap pydantic.ModelField."""

from pydantic.main import ModelField


class PygasusField:

    """Pygasus field, wrapping around a Pydantic ModelField."""

    __slots__ = ("__field__", "__model__", "__storage__")

    def __init__(self, field: ModelField):
        self.__field__ = field
        self.__model__ = None
        self.__storage__ = None

    def __getattr__(self, key):
        if key in type(self).__slots__:
            raise AttributeError
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
