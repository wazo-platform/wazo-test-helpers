# Copyright 2018-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from typing import Any

import sqlalchemy

from sqlalchemy.sql import text

logger = logging.getLogger(__name__)


class DBUserClient:

    @classmethod
    def build(cls, user: str, password: str, host: str, port: int, db: str | None = None) -> DBUserClient:
        return cls(f"postgresql://{user}:{password}@{host}:{port}/{db}")

    def __init__(self, db_uri: str) -> None:
        self._db_uri = db_uri
        self._engine = sqlalchemy.create_engine(self._db_uri)

    def is_up(self) -> bool:
        try:
            self._engine.connect()
            return True
        except Exception as e:
            logger.debug('Database is down: %s', e)
            return False

    def execute(self, query: str, **kwargs: Any) -> None:
        with self._engine.connect() as connection:
            connection.execute(text(query), **kwargs)
