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

"""Helpers to select Pygasus fields."""

from pydantic import BaseModel
from pydantic.fields import SHAPE_SINGLETON

from pygasus.field.base import PygasusField
from pygasus.field.one2one import One2OneField


def update_pygasus_field(field: PygasusField) -> PygasusField:
    """Return a sub-class of PygasusField for this field.

    Args:
        field (ModelField): the model's fieldl itself.

    """
    model = field.__model__
    storage = field.__storage__
    pydantic = field.__field__
    if pydantic.shape == SHAPE_SINGLETON and issubclass(
        pydantic.type_, BaseModel
    ):
        # Check that the back field is a one-relation too.
        back = storage.get_back_field(model, pydantic, pydantic.type_)
        if back.shape == SHAPE_SINGLETON:
            # That's a one-to-one relation.
            new_field = One2OneField(field)
            model.__pygasus__[pydantic.name] = new_field
            setattr(model, pydantic.name, new_field)
            new_field.bind(model, storage)
            return new_field

    return field
