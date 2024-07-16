# Copyright 2023-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class FileSystemClient:
    user = 'root'
    group = 'root'

    def __init__(
        self,
        execute: Callable[..., Any],
        service_name: str | None = None,
        root: bool = False,
    ) -> None:
        self.execute = execute
        self.service_name = service_name
        self.root = root

    def create_file(
        self,
        path: str | Path,
        content: str = 'content',
        mode: str = '666',
        root: bool = False,
    ) -> None:
        command = ['sh', '-c', f'cat <<EOF > {path}\n{content}\nEOF']
        self.execute(command, service_name=self.service_name)
        command = ['chmod', mode, str(path)]
        self.execute(command, service_name=self.service_name)
        if not root and not self.root:
            command = ['chown', f'{self.user}:{self.group}', str(path)]
            self.execute(command, service_name=self.service_name)

    def remove_file(self, path: str | Path) -> None:
        command = ['rm', '-f', f'{path}']
        self.execute(command, service_name=self.service_name)

    @contextmanager
    def file_(
        self,
        path: str | Path,
        content: str = 'content',
        mode: str = '666',
        root: bool = False,
    ) -> Generator[None, None, None]:
        self.create_file(path, content, mode, root)
        try:
            yield
        finally:
            self.remove_file(path)
