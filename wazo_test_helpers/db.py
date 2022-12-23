# Copyright 2018-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sqlalchemy

from sqlalchemy.sql import text

logger = logging.getLogger(__name__)


class DBUserClient:

    @classmethod
    def build(cls, user, password, host, port, db=None):
        return cls(f"postgresql://{user}:{password}@{host}:{port}/{db}")

    def __init__(self, db_uri):
        self._db_uri = db_uri
        self._engine = sqlalchemy.create_engine(self._db_uri)

    def is_up(self):
        try:
            self._engine.connect()
            return True
        except Exception as e:
            logger.debug('Database is down: %s', e)
            return False

    def execute(self, query, **kwargs):
        with self._engine.connect() as connection:
            connection.execute(text(query), **kwargs)
