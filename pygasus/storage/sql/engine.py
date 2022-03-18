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

"""SQLAlchemy storage engine for Pygasus."""

from datetime import date, datetime
import enum
import operator
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from uuid import UUID


try:
    from typing import get_origin
except ImportError:
    from typing_compat import get_origin

from pydantic import EmailStr
from pydantic.fields import SHAPE_LIST
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    create_engine,
    event,
)
from sqlalchemy.sql import select

from pygasus.field.helpers import update_pygasus_field
from pygasus.model import Field, Model, Sequence
from pygasus.storage.abc import AbstractStorageEngine
from pygasus.storage.sql.query_builder import SQLQueryBuilder

SQL_TYPES = {
    bool: Boolean,
    bytes: LargeBinary,
    date: Date,
    datetime: DateTime,
    float: Float,
    int: Integer,
    str: Text,
    UUID: Text,
    EmailStr: Text,
}


class SQLStorageEngine(AbstractStorageEngine):

    """Storage engine for SQLAlchemy.

    This storage engine only supports Sqlite at the moment.

    """

    def __init__(self):
        super().__init__()
        self.query_builder = SQLQueryBuilder(self)
        self.file_name = None
        self.memory = False
        self.tables = {}
        self.uniques = {}
        self.futures = set()

    def init(
        self,
        file_name: Union[str, Path, None] = None,
        memory: bool = False,
        logging: Union[bool, Callable[[str, Tuple[Any]], None]] = True,
    ):
        """Initialize the storage engine.

        Args:
            file_name (str or Path): the file_name in which the database
                    is stored, or will be stored.  It can be a relative
                    or absolute file name.  If you want to just store
                    in memory, don't specify a file name and just set
                    the `memory` argument to `True`.
            memory (bool): whether to store this database in memory or
                    not?  If `True`, the file name is ignored.
            logging (bool): if True (the default), log SQL queries.

        """
        self.file_name = file_name if not memory else None
        self.memory = memory
        self.logging = logging

        # Connect to the database.
        if memory:
            sql_file_name = ":memory:"
        else:
            if isinstance(file_name, str):
                file_name = Path(file_name)

            assert isinstance(file_name, Path)
            if file_name.absolute():
                sql_file_name = str(file_name)
            else:
                sql_file_name = str(file_name.resolve())
            self.file_name = file_name
        self.engine = create_engine(f"sqlite:///{sql_file_name}")

        # Add a function to override lower, as it only supports
        # ASCII in sqlite3.
        @event.listens_for(self.engine, "connect")
        def setup_lower(dbapi_connection, conn_rec):
            dbapi_connection.create_function("pylower", 1, str.lower)

        # Intercept requests to log them, if set.
        @event.listens_for(self.engine, "before_cursor_execute")
        def log_query(conn, cr, statement, parameters, *_):
            log = self.logging
            log = log if callable(log) else print
            if self.logging:
                log(statement.strip(), parameters)

        self.connection = self.engine.connect()
        self.metadata = MetaData()
        self.tables = {}

    def close(self):
        """Close the connection to the storage engine."""
        self.models = {}

    def destroy(self):
        """Close and destroy the storage engine."""
        self.close()
        if self.file_name:
            self.file_name.unlink()

    def bind(self, models: Optional[Set[Type[Model]]] = None):
        """Bind the speicifed models to this controller.

        If the models aren't specified, then bind every model found
        in the default set.  This is often desirable, although adding
        every model means that one should only import a class in order
        for it to be present.  TalisMUD has a lt of systems of dynamic
        importing, which can make this choice complicated in some
        instances.

        """
        super().bind(models)
        self.metadata.create_all(self.engine)

    def bind_model(self, model: Type[Model], names: Dict[str, Any]):
        """Bind this controller to a specific model.

        Args:
            model (subclass of Model): the model to bind.
            names (dict): the dictionary (name: model) of other models.

        """
        columns = []

        # Browse model fields, creating columsn, indexes and constraints.
        indexes = []
        for name, field in model.__fields__.items():
            model.__pygasus__[name].bind(model, self)
            update_pygasus_field(model.__pygasus__[name])
            pygasus = model.__pygasus__[name]
            o_type = field.outer_type_
            f_type = field.type_
            info = field.field_info
            origin = get_origin(o_type)

            # If it's a custom field, use that instead.
            custom = info.extra.get("custom_class")
            if custom:
                f_type = self.add_custom_field_to_model(custom, model, field)

            if origin is list or o_type is Sequence[f_type]:
                # Analyze the back field.  If it's a list too, an
                # intermediate table should be created.
                field.outer_type_ = Sequence[f_type]
                field.default = Sequence[f_type](
                    left_model=model,
                    left_field=field,
                    right_model=f_type,
                    right_field=self.get_back_field(model, field, f_type),
                )
                continue
            elif isinstance(f_type, type) and issubclass(f_type, Model):
                # If the field is optional (and back isn't) do not add.
                back = self.get_back_field(model, field, f_type)

                # Choose the owner field.
                extra = info.extra
                back_extra = back.field_info.extra
                if extra.get("owner") and not back_extra.get("owner"):
                    extra["owner"] = True
                    back_extra["owner"] = False
                elif not extra.get("owner") and back_extra.get("owner"):
                    extra["owner"] = False
                    back_extra["owner"] = True
                elif pygasus.required and not back.required:
                    extra["owner"] = True
                    back_extra["owner"] = False
                elif not pygasus.required and back.required:
                    extra["owner"] = False
                    back_extra["owner"] = True

                if not extra.get("owner"):
                    continue

                # Create foreign key fields.
                to_name = getattr(
                    f_type.__config__, "model_name", f_type.__name__.lower()
                )
                primary_keys = {
                    name: field
                    for name, field in f_type.__fields__.items()
                    if field.field_info.extra.get("primary_key")
                }

                for pname, pfield in primary_keys.items():
                    columns.append(
                        Column(
                            f"{name}_{pname}",
                            None,
                            ForeignKey(f"{to_name}.{pname}"),
                            nullable=not field.required,
                        )
                    )

                # Add sort options.
                if back.shape == SHAPE_LIST:
                    columns.append(
                        Column(
                            f"{name}__index",
                            Integer,
                            nullable=False,
                        )
                    )
                continue

            # Handle enumerations here.
            if isinstance(f_type, type) and issubclass(f_type, enum.Enum):
                e_type = type(list(f_type)[0].value)
                if not all(
                    isinstance(member.value, e_type) for member in f_type
                ):
                    raise ValueError(
                        f"the enumeration {f_type} contains members 3"
                        "of different types"
                    )
                invalid_member = info.extra.get("invalid_member", "INVALID")
                if isinstance(invalid_member, str):
                    invalid = getattr(f_type, invalid_member, ...)
                else:
                    invalid = invalid_member

                if invalid is ...:
                    raise ValueError(
                        f"field {model.__name__}.{name}: no invalid member "
                        f"is provided for the enumeration {f_type}.  The "
                        "invalid member is required when using enumerations "
                        "to let Pygasus know what to do if the stored "
                        "enumeration member doesn't match the enumeration "
                        "class.  Provide one with "
                        "Field(..., invalid_member=MyEnum.INVALID)"
                    )
                f_type = e_type

            sql_type = SQL_TYPES.get(f_type)
            if sql_type is None:
                raise ValueError(f"unknown type: {name} ({f_type})")
            else:
                extra = info.extra
                primary_key = extra.get("primary_key", False)
                unique = extra.get("unique", False)
                index = extra.get("index", False)
                column = Column(
                    name,
                    sql_type,
                    primary_key=primary_key,
                    nullable=not field.required,
                )
            columns.append(column)

            if unique or index:
                indexes.append(Index(f"idx_{name}", name, unique=unique))

        # Add unique constraints on several columns.
        columns += indexes
        for uniques in getattr(model.__config__, "unique", ()):
            if isinstance(uniques, str):
                uniques = uniques.split()

            if any(name not in model.__fields__ for name in uniques):
                raise ValueError(
                    f"the unique constraint {uniques!r} on model {model} "
                    "is invalid, unknown colomn name"
                )
            columns.append(
                Index(f"idx_{'_'.join(uniques)}", *uniques, unique=True)
            )

        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        if model_name in self.models:
            raise ValueError(
                f"the model {model} of name {model_name!r} conflicts with "
                f"the model {self.models[model_name]} which has the same "
                "name.  Please provide a different name to any of "
                "them, either through setting the 'model_name' "
                "configuration variable in the model or through "
                "changing one of their class names."
            )

        self.models[model_name] = model
        self.tables[model_name] = Table(model_name, self.metadata, *columns)

    def insert(
        self,
        model: Type[Model],
        attrs: Dict[str, Any],
        additional: Optional[Dict[str, Any]] = None,
    ) -> Model:
        """Add a new row for this model.

        The model is used to determine the collection in storage.

        Args:
            model (subclass of Model): the model class.
            attrs (dict): the model attributes.
            additional (opt dict): other attributes, not used in the model.

        Returns:
            obj (Model): the new object.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        exclude = set()
        linked = set()
        sql = {}
        for name, field in model.__fields__.items():
            info = field.field_info
            o_type = field.outer_type_
            f_type = field.type_
            pygasus = getattr(model, field.name)
            if o_type is Sequence[f_type]:
                exclude.add(name)
                linked.add(name)
                continue

            custom = self.custom_fields.get((model, field.name))
            if custom:
                value = attrs[name]
                sql[name] = custom.to_storage(value)

            if issubclass(f_type, Model):
                right = attrs.get(name, field.get_default())
                if not isinstance(right, Model):  # Skip here (non valid).
                    exclude.add(name)
                    continue

                primary_keys = {
                    name: field
                    for name, field in f_type.__fields__.items()
                    if field.field_info.extra.get("primary_key")
                }

                for pname, pfield in primary_keys.items():
                    sql[f"{name}_{pname}"] = getattr(right, pname)

                exclude.add(name)
                continue

            if issubclass(f_type, enum.Enum):
                sql[name] = attrs[name].value

            # Convert the field, if necessary.
            method = getattr(
                self, f"{o_type.__name__.lower()}_to_storage", None
            )
            if method:
                sql[name] = method(model, field, attrs[name])

            pk = info.extra.get("primary_key", False)
            if pk and issubclass(f_type, int):
                attrs[name] = 1
                exclude.add(name)

        if additional:
            sql.update(additional)

        # Validate the model object.
        obj = model(**attrs)
        for name, attr in attrs.items():
            pygasus = getattr(model, name)
            pygasus.validate_update(obj, None, attr)

        for name, attr in attrs.items():
            pygasus = getattr(model, name)
            pygasus.perform_update(obj, None, attr)

        # Create a row.
        table = self.tables[model_name]
        insert = table.insert().values(dict(obj.dict(exclude=exclude), **sql))
        result = self.connection.execute(insert)

        primary_keys = iter(result.inserted_primary_key)
        obj._exists = False
        pks = []
        for name, field in model.__fields__.items():
            info = field.field_info
            f_type = field.type_
            pk = info.extra.get("primary_key", False)
            if pk and issubclass(f_type, int):
                value = next(primary_keys)
                setattr(obj, name, value)
                pks.append(value)
            elif name in linked:
                # This is a linked field, we need to set the parent.
                getattr(obj, name).parent = obj

        obj._exists = True
        self.cache[(model,) + tuple(pks)] = obj

        for name, field in model.__fields__.items():
            info = field.field_info
            o_type = field.outer_type_
            f_type = field.type_
            pk = info.extra.get("primary_key", False)
            if o_type is Sequence[f_type]:
                obj._exists = False
                setattr(getattr(obj, name), "parent", obj)
                obj._exists = True

        return obj

    def insert_at(
        self,
        model: Type[Model],
        attrs: Dict[str, Any],
        index: int,
        additional: Optional[Dict[str, Any]] = None,
    ) -> Model:
        """Add a new row at this index for this model.

        The model is used to determine the collection in storage.

        Args:
            model (subclass of Model): the model class.
            attrs (dict): the model attributes.
            index (int): the index at which to add this object.
            additional (opt dict): other attributes, not used in the model.

        Returns:
            obj (Model): the new object.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        table = self.tables[model_name]
        additional = {}
        for name, field in model.__fields__.items():
            o_type = field.outer_type_
            f_type = field.type_
            if issubclass(f_type, Model) and o_type is not Sequence[f_type]:
                right = attrs[name]
                cmp = operator.le if index < 0 else operator.ge
                where = [cmp(getattr(table.c, f"{name}__index"), index)]
                primary_keys = {
                    name: field
                    for name, field in f_type.__fields__.items()
                    if field.field_info.extra.get("primary_key")
                }

                for pname, pfield in primary_keys.items():
                    where.append(
                        getattr(table.c, f"{name}_{pname}")
                        == getattr(right, pname)
                    )

                # Create and send the query.
                col_name = f"{name}__index"
                col = getattr(table.c, col_name)
                new_value = (col - 1) if index < 0 else (col + 1)
                update = (
                    table.update()
                    .where(*where)
                    .values({getattr(table.c, col_name): new_value})
                )
                self.connection.execute(update)
                additional[col_name] = index
        return self.insert(model, attrs, additional)

    def select(self, model: Type[Model], query):
        """Select one or more model instances with the specified query.

        Args:
            model (subclass of Model): the model object.
            query: the query object by which to filter.

        Returns:
            instances (list of Model): the model isntances or None.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        table = self.tables[model_name]
        models = [model]
        columns, tables = self._get_columns_for(model)
        sql = select(*columns)
        for join in tables:
            sql = sql.join(table)
        sql = sql.where(query)

        # Send the query.
        rows = self.connection.execute(sql).fetchall()
        return [
            self._build_objects_from_row(dict(row), models, first=True)
            for row in rows
        ]

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
        # First, check whether this object is in cache.
        pks = []
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        table = self.tables[model_name]
        models = [model]
        for name, field in model.__fields__.items():
            info = field.field_info
            o_type = field.outer_type_
            f_type = field.type_
            pk = info.extra.get("primary_key", False)
            if pk:
                value = kwargs.get(name, ...)
                if value is not ...:
                    pks.append(value)
            elif issubclass(f_type, Model) and o_type is not Sequence[f_type]:
                # Join up.
                models.append(f_type)

        obj = self.cache.get((model,) + tuple(pks))
        if obj is not None:
            return obj

        columns, tables = self._get_columns_for(model)
        query = select(*columns)
        for join in tables:
            query = query.join(join)
        where = []
        for column, value in kwargs.items():
            method = getattr(
                self, f"{type(value).__name__.lower()}_to_storage", None
            )
            if method:
                value = method(model, model.__fields__[column], value)

            where.append(getattr(table.c, column) == value)
        query = query.where(*where)

        # Send the query.
        rows = self.connection.execute(query).fetchall()
        if len(rows) == 0 or len(rows) < 1:
            return None

        row = dict(rows[0])
        obj = self._build_objects_from_row(row, models, first=True)
        return obj

    def get_related(self, sequence: Sequence) -> List[Model]:
        """Retrieve the related objects from a sequence.

        The sequence is a sequence that represents various objects
        related to the parent model.

        Args:
            sequence (Sequence): the sequence.

        Returns:
            models (list of Model): the models.

        """
        # Create a filter query.
        parent = sequence.parent
        left_model = sequence.left_model
        right_model = sequence.right_model
        pks = {}
        left_model_name = getattr(
            left_model.__config__, "model_name", left_model.__name__.lower()
        )
        right_model_name = getattr(
            right_model.__config__, "model_name", right_model.__name__.lower()
        )
        table = self.tables[right_model_name]
        for name, field in right_model.__fields__.items():
            info = field.field_info
            pk = info.extra.get("primary_key", False)
            if pk:
                value = getattr(parent, name, ...)
                if value is not ...:
                    pks[f"{left_model_name}_{name}"] = value

        columns, tables = self._get_columns_for(right_model)
        query = select(*columns)
        for join in tables:
            query = query.join(join)

        where = []
        for column, value in pks.items():
            where.append(getattr(table.c, column) == value)
        query = query.where(*where)

        # Add ordering.
        query = query.order_by(getattr(table.c, f"{left_model_name}__index"))
        # Send the query.
        rows = self.connection.execute(query).fetchall()
        objs = [
            self._build_objects_from_row(dict(row), [right_model], first=True)
            for row in rows
        ]
        return objs

    def update(
        self,
        model: Type["Model"],
        instance: "Model",
        key: str,
        old_value: Any,
        new_value: Any,
    ):
        """Update an instance attribute.

        Args:
            model (subclass of Model): the model class.
            instance (Model): the model object.
            key (str): the name of the attribute to modify.
            old_value (Any): the value before the modification.
            new_value (Any): the value after the modification.
            check_update (bool): if True (default), check the update.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        sql_table = self.tables[model_name]
        sql_primary_keys = []
        for name, field in model.__fields__.items():
            info = field.field_info
            pk = info.extra.get("primary_key", False)
            if pk:
                value = getattr(instance, name)
                if isinstance(value, enum.Enum):
                    value = value.value

                # Handle other field types.
                method = getattr(
                    self, f"{type(value).__name__.lower()}_to_storage", None
                )
                if method:
                    value = method(model, field, value)

                # Handle custom fields.
                custom = self.custom_fields.get((model, field.name))
                if custom:
                    value = custom.to_storage(value)
                sql_primary_keys.append(getattr(sql_table.c, name) == value)

        field = model.__fields__[key]
        # Handles enum field.
        if isinstance(new_value, enum.Enum):
            new_value = new_value.value

        # Handle other field types.
        method = getattr(
            self, f"{type(new_value).__name__.lower()}_to_storage", None
        )
        if method:
            new_value = method(model, field, new_value)

        # Handle custom fields.
        custom = self.custom_fields.get((model, field.name))
        if custom:
            new_value = custom.to_storage(new_value)

        sql_columns = {key: new_value}
        f_type = field.type_
        pygasus = model.__pygasus__[field.name]
        if issubclass(f_type, Model):
            if not field.field_info.extra.get("owner", True) and new_value:
                old_value = getattr(new_value, pygasus.__back__.name, None)
                return self.update(
                    type(new_value),
                    new_value,
                    pygasus.__back__.name,
                    old_value,
                    instance,
                )

            sql_columns = {}
            linked_keys = {
                linked_name: linked_field
                for linked_name, linked_field in f_type.__fields__.items()
                if linked_field.field_info.extra.get("primary_key")
            }

            for pname, pfield in linked_keys.items():
                value = new_value and getattr(new_value, pname) or None
                sql_columns[f"{field.name}_{pname}"] = value

        # Check that this update can be performed.
        pygasus.validate_update(instance, old_value, new_value)
        pygasus.perform_update(instance, old_value, new_value)

        # Send the query.
        update = (
            sql_table.update().where(*sql_primary_keys).values(**sql_columns)
        )
        self.connection.execute(update)

    def delete(self, model: Type[Model], instance: Model):
        """Delete the specified model.

        Args:
            model (subclass of Model): the model class.
            instance (Model): the model instance.

        The model also is removed from cache.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        sql_table = self.tables[model_name]
        sql_primary_keys = []
        pks = []
        for name, field in model.__fields__.items():
            info = field.field_info
            pk = info.extra.get("primary_key", False)
            pygasus = model.__pygasus__[name]
            if pk:
                value = getattr(instance, name)
                # Convert other field types.
                method = getattr(
                    self, f"{type(value).__name__.lower()}_to_storage", None
                )
                if method:
                    value = method(model, field, value)
                sql_primary_keys.append(getattr(sql_table.c, name) == value)
                pks.append(value)

            pygasus.validate_delete(instance)

        # Remove this object from cache.
        self.cache.pop((model,) + tuple(pks), None)

        # Send the query.
        delete = sql_table.delete().where(*sql_primary_keys)
        self.connection.execute(delete)

        # Apply other updates if necessary.
        for pygasus in model.__pygasus__.values():
            pygasus.perform_delete(instance)

    def bulk_delete(self, model: Type[Model], query) -> int:
        """Select one or more models with the specified query and delete them.

        Args:
            model (subclass of Model): the model object.
            query: the query object by which to filter.

        Returns:
            number (int): the number of deleted rows.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        table = self.tables[model_name]
        pks = []
        for name, field in model.__fields__.items():
            info = field.field_info
            pk = info.extra.get("primary_key", False)
            if pk:
                pks.append(name)

        sql = table.delete().where(query)

        # Perform a select (this will be an additional query, but
        # we need to safely invalidate the cache).
        for obj in self.select(model, query):
            specific_pks = []
            for name in pks:
                value = getattr(obj, name)
                # Convert other field types.
                method = getattr(
                    self, f"{type(value).__name__.lower()}_to_storage", None
                )
                if method:
                    value = method(model, field, value)
                specific_pks.append(value)
            self.cache.pop((model,) + tuple(specific_pks), None)

        # Send the query.
        ret = self.connection.execute(sql)
        return ret.rowcount

    def _get_columns_for(
        self, model: Type[Model], recursion=True
    ) -> Tuple[Column]:
        """Return the relevant columns for the specified model.

        Args:
            model (subclass of Model): the model.

        Returns:
            columns (tuple of Column): the labelled columns for this model.

        """
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        columns = []
        table = self.tables[model_name]
        tables = []
        for name, field in model.__fields__.items():
            o_type = field.outer_type_
            f_type = field.type_
            if issubclass(f_type, Model) and o_type is not Sequence[f_type]:
                # Join up.
                if recursion:
                    tables.append(
                        self.tables[
                            getattr(
                                f_type.__config__,
                                "model_name",
                                f_type.__name__.lower(),
                            )
                        ]
                    )

                    other_columns, other_tables = self._get_columns_for(
                        f_type, recursion=False
                    )
                    columns.extend(other_columns)
                    tables.extend(other_tables)
            elif o_type is not Sequence[f_type]:
                columns.append(
                    getattr(table.c, name).label(f"{model_name}_{name}")
                )

        return columns, tables

    def _build_objects_from_row(
        self,
        row: Dict[str, Any],
        models: Tuple[Type[Model]],
        first: bool = True,
        done: Optional[Tuple[Type[Model]]] = None,
    ) -> Union[Model, Tuple[Model]]:
        """Create one or more model objects from this row.

        Args:
            row (dict): a dictionary containing row data.
            models (tuple): the tuple of subclasses of models.
            first (bool): if True (the default), return only the first model.
            done (opt): tuple of models that were already processed.

        Returns:
            model or models: the created model(s).

        """
        done = done or ()
        objs = []
        done = list(done)
        customs = []
        for model in models:
            done.append(model)
            model_name = getattr(
                model.__config__, "model_name", model.__name__.lower()
            )

            # Browse the model's fields.
            attrs = {}
            others = []
            pks = []
            for name, field in model.__fields__.items():
                info = field.field_info
                o_type = field.outer_type_
                f_type = field.type_
                pk = info.extra.get("primary_key", False)
                value = row.get(f"{model_name}_{name}", ...)
                custom = self.custom_fields.get((model, field.name))
                if pk:
                    if value is not ...:
                        pks.append(value)

                    # Convert the field, if necessary.
                    value = row[f"{model_name}_{name}"]
                    method = getattr(
                        self,
                        f"{type(value).__name__.lower()}_from_storage",
                        None,
                    )
                    if method:
                        value = method(model, field, value)

                    attrs[name] = value
                elif custom:
                    value = custom.to_field(value)
                    customs.append((value, name))
                    attrs[name] = value
                elif (
                    isinstance(f_type, type)
                    and issubclass(f_type, Model)
                    and o_type is not Sequence[f_type]
                ):
                    if not field.required:
                        attrs[name] = field.get_default()

                        # Prepare the future.
                        pkeys = tuple(
                            row[f"{model_name}_{pk.name}"]
                            for pk in model.__fields__.values()
                            if pk.field_info.extra.get("primary_key", False)
                        )
                        link_pkeys = tuple(
                            row[f"{name}_{pk.name}"]
                            for pk in f_type.__fields__.values()
                            if pk.field_info.extra.get("primary_key", False)
                        )
                        self.futures.add(
                            (model, pkeys, name, f_type, link_pkeys)
                        )
                    else:
                        obj = self._build_objects_from_row(
                            row, (f_type,), done=tuple(done)
                        )
                        others.append(obj)
                        attrs[name] = obj

                        # Check whether this update would be possible.
                        pygasus = model.__pygasus__[name]
                        pygasus.validate_update(model, None, obj)
                elif issubclass(f_type, enum.Enum):
                    try:
                        value = f_type(value)
                    except ValueError:
                        invalid_key = getattr(
                            model.__config__, "invalid_enum_key", "INVALID"
                        )
                        value = getattr(f_type, invalid_key)
                    finally:
                        attrs[name] = value
                elif o_type is not Sequence[f_type]:
                    value = row[f"{model_name}_{name}"]
                    method = getattr(
                        self,
                        f"{type(value).__name__.lower()}_from_storage",
                        None,
                    )
                    if method:
                        value = method(model, field, value)

                    attrs[name] = value

            obj = self.cache.get((model,) + tuple(pks))
            if obj is not None:
                objs.append(obj)
            else:
                obj = model(**attrs)
                for field, name in customs:
                    field.parent = obj
                    field.field = name
                self.cache[(model,) + tuple(pks)] = obj
                objs.append(obj)
                for name, field in model.__fields__.items():
                    info = field.field_info
                    o_type = field.outer_type_
                    f_type = field.type_
                    pk = info.extra.get("primary_key", False)
                    if o_type is Sequence[f_type]:
                        obj._exists = False
                        col = getattr(obj, name)
                        col.parent = obj
                        obj._exists = True

                # Update Pygasus fields.
                for pygasus in type(obj).__pygasus__.values():
                    value = attrs.get(pygasus.name)
                    pygasus.perform_update(obj, None, value)

            objs.extend(others)

        self._apply_futures()
        if not objs:
            objs = [None]

        return objs[0] if first else objs

    # Type conversions.
    def uuid_from_storage(
        self, model: Model, field: Field, value: str
    ) -> UUID:
        """Convert a UUID hex to a UUID object."""
        return UUID(value)

    def uuid_to_storage(self, model: Model, field: Field, value: UUID) -> str:
        """Convert a UUID to a str representation."""
        return value.hex

    def _apply_futures(self):
        """Try to apply the futures."""
        for model, pks, key, link_model, link_pks in tuple(self.futures):
            obj = self.cache.get((model,) + pks)
            to_link = self.cache.get((link_model,) + link_pks)
            if obj is not None and to_link is not None:
                obj._exists = False
                setattr(obj, key, to_link)
                obj._exists = True
                self.futures.discard((model, pks, key, link_model, link_pks))
