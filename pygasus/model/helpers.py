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

"""Helper functions for models."""

from typing import Any, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pygasus.model.base import Model  # pragma: no cover


def get_model_qualname(model: Type["Model"]) -> str:
    """Return the model's qualname with its module.

    Args:
        model (subclass of Model): the class.

    Returns:
        qualname (str): the qualname with its module.

    """
    return f"{model.__module__}.{model.__qualname__}"


def get_primary_keys(
    model: "Model",
    include_model_name: bool = False,
) -> Dict[str, Any]:
    """Get the primary keys of this object and return a dictionary.

    Args:
        model (Model): the model from which to retrieve primary key fields.
        include_model_name (bool): include the model name in the dictionary.

    Returns:
        A dictionary.  The first entry, `__name__`, is the model
        name, if `include_model_name` has been set to `True`.

    """
    keys = {}
    model_cls = type(model)
    if include_model_name:
        keys["__name__"] = get_model_qualname(model_cls)

    # Add the primary key fields and their values.
    for name, field in model.__fields__.items():
        if field.field_info.extra.get("primary_key", False):
            value = getattr(model, name, ...)
            if value is ...:
                raise ValueError(
                    f"the model of class {model_cls} should have "
                    f"a field named {name!r}, this is not the case"
                )
            keys[name] = value

    return keys
