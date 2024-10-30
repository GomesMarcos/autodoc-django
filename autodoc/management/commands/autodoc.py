import ast

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate MermaidJS (https://mermaid.live/edit) flowchart auto documentation to django apps' files"

    def handle(self, *args, **kwargs):
        print(args, kwargs)
        if args in settings.INSTALLED_APPS:
            print('qwe')
        else:
            print(f'\033[91m\n\nInvalid arg: {args} \n\n\033[0m')

    def generate_mermaid_diagram(self, filename):
        """Gera um diagrama Mermaid para o arquivo Python especificado.

        Args:
            filename (str): Caminho completo para o arquivo Python.

        Returns:
            str: Código Mermaid gerado.
        """

        with open(filename, 'r') as f:
            tree = ast.parse(f.read())

        mermaid_code = 'flowchart\n'
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                mermaid_code += f'{node.name}(Function)\n'

        return mermaid_code

    def main(self):
        """Generate MermaidJS diagrams for specified Python files.

        This method processes a list of Python files and generates corresponding
        MermaidJS diagrams, saving them to files with a .mmd extension. It is
        intended to automate the documentation of Django applications by creating
        visual representations of their structure.

        Args:
            self: The instance of the class.

        Examples:
            To use this method, simply type ./manage.py autodoc <app_name> || <specified_file_path>
        """

        # TODO: get app name by arg and it's views.py, admin.py files.
        # TODO: get specified file's paths list
        python_files = ['autodoc.py']

        for file in python_files:
            mermaid_code = self.generate_mermaid_diagram(file)
            with open(f'{file}.mmd', 'w') as f:
                f.write(mermaid_code)
