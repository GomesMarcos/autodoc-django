import os
from typing import List

from django.core.management.base import BaseCommand


class AutodocCommandUtils(BaseCommand):
    """
    Classe utilitária para gerar diagramas de classes e funções.
    """

    def process_app(self, app_name: str):
        """
        Encontra os caminhos dos arquivos e gera diagramas.
        """
        # Arquivos a serem analisados
        app_path = self.get_app_path(app_name)
        views_path = os.path.join(app_path, 'views')
        admin_path = os.path.join(app_path, 'admin')
        tasks_path = os.path.join(app_path, 'tasks')

        # Gera documentação se os arquivos existirem
        if os.path.isdir(views_path):
            for file in os.listdir(views_path):
                if not file.startswith('__') and file.endswith('.py'):
                    self.generate_views_diagram(
                        os.path.join(views_path, file), app_name
                    )
        elif os.path.exists(f'{views_path}.py'):
            self.generate_views_diagram(f'{views_path}.py', app_name)

        if os.path.isdir(admin_path):
            for file in os.listdir(admin_path):
                if not file.startswith('__') and file.endswith('.py'):
                    self.generate_admin_diagram(
                        os.path.join(admin_path, file), app_name
                    )
        elif os.path.exists(f'{admin_path}.py'):
            self.generate_admin_diagram(f'{admin_path}.py', app_name)

        if os.path.isdir(tasks_path):
            for file in os.listdir(tasks_path):
                if not file.startswith('__') and file.endswith('.py'):
                    self.generate_tasks_diagram(
                        os.path.join(tasks_path, file), app_name
                    )
        elif os.path.exists(f'{tasks_path}.py'):
            self.generate_tasks_diagram(f'{tasks_path}.py', app_name)

    def get_app_path(self, app_name: str):
        """Retorna o caminho do app Django."""
        module = __import__(app_name)
        if not module.__file__:
            raise ValueError(
                f'Não foi possível encontrar o caminho para o app {app_name}'
            )
        return os.path.dirname(module.__file__)

    def save_mermaid_diagram(self, mermaid_code: List[str], filename: str):
        """Salva o diagrama Mermaid em um arquivo."""
        if not self.validate_mermaid_code(mermaid_code):
            self.stdout.write(
                self.style.ERROR(
                    f'Diagrama Mermaid não existe para o arquivo: {filename}'
                )
            )
            return
        output_dir = 'docs/mermaid/flow'
        os.makedirs(output_dir, exist_ok=True)

        filepath = f'{output_dir}/{filename}.md'
        with open(filepath, 'w') as f:
            f.write('\n'.join(mermaid_code))
            f.write('\n```')

        self.stdout.write(
            self.style.SUCCESS(f'Diagrama Mermaid gerado com sucesso: {filepath}')
        )

    def validate_mermaid_code(self, mermaid_code: List[str]):
        """Validate inner code of mermaid diagram."""
        return bool(mermaid_code[2:])

    def generate_views_diagram(self, path, app_name):
        raise NotImplementedError

    def generate_admin_diagram(self, path, app_name):
        raise NotImplementedError

    def generate_tasks_diagram(self, path, app_name):
        raise NotImplementedError
