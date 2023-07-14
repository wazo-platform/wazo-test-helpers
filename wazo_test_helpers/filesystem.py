# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class FileSystemClient:
    user = 'root'
    group = 'root'

    def __init__(self, execute, service_name=None, root=False):
        self.execute = execute
        self.service_name = service_name
        self.root = root

    def create_file(self, path, content='content', mode='666', root=False):
        command = ['sh', '-c', f'cat <<EOF > {path}\n{content}\nEOF']
        self.execute(command, service_name=self.service_name)
        command = ['chmod', mode, path]
        self.execute(command, service_name=self.service_name)
        if not root and not self.root:
            command = ['chown', f'{self.user}:{self.group}', path]
            self.execute(command, service_name=self.service_name)

    def remove_file(self, path):
        command = ['rm', '-f', f'{path}']
        self.execute(command, service_name=self.service_name)
