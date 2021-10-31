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
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union


try:
    from typing import get_origin
except ImportError:
    from typing_compat import get_origin

from pydantic import EmailStr
from sqlalchemy import (
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

from pygasus.model import Model, Sequence
from pygasus.storage.abc import AbstractStorageEngine

SQL_TYPES = {
    bytes: LargeBinary,
    date: Date,
    datetime: DateTime,
    float: Float,
    int: Integer,
    str: Text,
    EmailStr: Text,
}


class SQLStorageEngine(AbstractStorageEngine):

    """Storage engine for SQLAlchemy.

    This storage engine only supports Sqlite at the moment.

    """

    def __init__(self):
        super().__init__()
        self.file_name = None
        self.memory = False
        self.tables = {}
        self.uniques = {}

    def init(
        self,
        file_name: Union[str, Path, None] = None,
        memory: bool = False,
        logging: bool = True,
    ):
        """
        Initialize the storage engine.

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
            if self.logging:
                print(statement.strip(), parameters)

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
            o_type = field.outer_type_
            f_type = field.type_
            origin = get_origin(o_type)
            if origin is list:
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
            elif issubclass(f_type, Model):
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
                        )
                    )
                continue

            sql_type = SQL_TYPES.get(f_type)
            if sql_type is None:
                raise ValueError(f"unknown type: {name} ({f_type})")
            else:
                extra = field.field_info.extra
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

    def insert(self, model: Type[Model], **kwargs):
        """Add a new row for this model.

        The model is used to determine the collection in storage.
        Keyword arguments are used to specify data for this new model.

        Args:
            model (subclass of Model): the model class.
            Additional keyword arguments are expected.

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
            if o_type is Sequence[f_type]:
                exclude.add(name)
                linked.add(name)
                continue

            if issubclass(f_type, Model):
                right = kwargs[name]
                primary_keys = {
                    name: field
                    for name, field in f_type.__fields__.items()
                    if field.field_info.extra.get("primary_key")
                }

                for pname, pfield in primary_keys.items():
                    sql[f"{name}_{pname}"] = getattr(right, pname)

                exclude.add(name)
                continue

            pk = info.extra.get("primary_key", False)
            if pk and issubclass(f_type, int):
                kwargs[name] = 1
                exclude.add(name)

        # Validate the model object.
        obj = model(**kwargs)

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

        columns = self._get_columns_for(model)
        query = select(*columns)
        where = []
        for column, value in kwargs.items():
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
        model = sequence.right_model
        pks = {}
        model_name = getattr(
            model.__config__, "model_name", model.__name__.lower()
        )
        table = self.tables[model_name]
        for name, field in model.__fields__.items():
            info = field.field_info
            pk = info.extra.get("primary_key", False)
            if pk:
                value = getattr(parent, name, ...)
                if value is not ...:
                    pks[name] = value

        columns = self._get_columns_for(model)
        query = select(*columns)
        where = []
        for column, value in pks.items():
            where.append(getattr(table.c, column) == value)
        query = query.where(*where)

        # Send the query.
        rows = self.connection.execute(query).fetchall()
        objs = [
            self._build_objects_from_row(dict(row), [model], first=True)
            for row in rows
        ]
        return objs

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
                sql_primary_keys.append(getattr(sql_table.c, name) == value)

        # Send the query.
        sql_columns = {key: new_value}
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
            if pk:
                value = getattr(instance, name)
                sql_primary_keys.append(getattr(sql_table.c, name) == value)
                pks.append(value)

        # Remove this object from cache.
        self.cache.pop((model,) + tuple(pks), None)

        # Send the query.
        delete = sql_table.delete().where(*sql_primary_keys)
        self.connection.execute(delete)

    def _get_columns_for(self, model: Type[Model]) -> Tuple[Column]:
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
        for name, field in model.__fields__.items():
            o_type = field.outer_type_
            f_type = field.type_
            if issubclass(f_type, Model) and o_type is not Sequence[f_type]:
                # Join up.
                columns.extend(self._get_columns_for(f_type))
            elif o_type is not Sequence[f_type]:
                columns.append(
                    getattr(table.c, name).label(f"{model_name}_{name}")
                )

        return columns

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
                if pk:
                    value = row.get(f"{model_name}_{name}", ...)
                    if value is not ...:
                        pks.append(value)
                    attrs[name] = row[f"{model_name}_{name}"]
                elif (
                    isinstance(f_type, type)
                    and issubclass(f_type, Model)
                    and o_type is not Sequence[f_type]
                ):
                    if f_type in done:
                        continue

                    obj = self._build_objects_from_row(
                        row, (f_type,), done=tuple(done)
                    )
                    others.append(obj)
                    attrs[name] = obj
                elif o_type is not Sequence[f_type]:
                    attrs[name] = row[f"{model_name}_{name}"]

            obj = self.cache.get((model,) + tuple(pks))
            if obj is not None:
                objs.append(obj)
            else:
                obj = model(**attrs)
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

            objs.extend(others)

        if not objs:
            objs = [None]

        return objs[0] if first else objs