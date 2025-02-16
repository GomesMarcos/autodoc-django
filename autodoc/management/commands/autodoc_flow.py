import ast
from typing import List

from django.conf import settings
from django.core.management.base import CommandError

from autodoc.utils import AutodocCommandUtils


class Command(AutodocCommandUtils):
    help = 'Generates automatic documentation in MermaidJS format for Django apps views, admins, and Celery tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            'app_names',
            nargs='+',
            type=str,
            help='Names of the Django apps to document',
        )

    def handle(self, *args, **options):
        for app_name in options['app_names']:
            if app_name not in settings.INSTALLED_APPS:
                raise CommandError(f'App "{app_name}" is not in INSTALLED_APPS')

            self.process_app(app_name)

    def parse_file(self, filename: str) -> ast.AST:
        """Parses a Python file."""
        with open(filename, 'r') as f:
            return ast.parse(f.read())

    def generate_views_diagram(self, filename: str, app_name: str):
        """Generates a Mermaid diagram for views."""
        tree = self.parse_file(filename)

        mermaid_code = ['```mermaid', 'flowchart TD']
        node_counter = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Identifica views baseadas em classes
                bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                if any(base.endswith('View') for base in bases):
                    class_id = f'class_{node.name}'
                    mermaid_code.append(f'    {class_id}[{node.name}]')

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_id = f'method_{node.name}_{item.name}'
                            mermaid_code.append(
                                f'    {class_id} --> {method_id}[{item.name}]'
                            )

                            # Analisa o corpo do método
                            for stmt in item.body:
                                node_counter = self._analyze_statement(
                                    stmt, method_id, mermaid_code, node_counter
                                )
        self.save_mermaid_diagram(
            mermaid_code, f"{app_name}_{filename.split('/')[-1].split('.')[0]}"
        )

    def _analyze_statement(
        self, stmt, parent_id: str, mermaid_code: List[str], counter: int
    ) -> int:
        """Analyzes a statement and adds it to the diagram."""
        if isinstance(stmt, ast.If):
            counter += 1
            if_id = f'if_{counter}'
            mermaid_code.append(
                f'    {parent_id} --> {if_id}{{if {self._get_condition_text(stmt.test)}}}'
            )

            # Analisa o bloco if
            for body_stmt in stmt.body:
                counter = self._analyze_statement(
                    body_stmt, if_id, mermaid_code, counter
                )

            # Analisa o bloco else se existir
            if stmt.orelse:
                counter += 1
                else_id = f'else_{counter}'
                mermaid_code.append(f'    {if_id} --> {else_id}[else]')
                for else_stmt in stmt.orelse:
                    counter = self._analyze_statement(
                        else_stmt, else_id, mermaid_code, counter
                    )

        elif isinstance(stmt, ast.Call):
            counter += 1
            call_id = f'call_{counter}'
            func_name = self._get_call_text(stmt)
            mermaid_code.append(f'    {parent_id} --> {call_id}[{func_name}]')

        elif isinstance(stmt, ast.Return):
            counter += 1
            return_id = f'return_{counter}'
            return_text = self._get_return_text(stmt)
            mermaid_code.append(
                f'    {parent_id} --> {return_id}{self._handle_return_text(return_text)}'
            )

        return counter

    def _handle_return_text(self, return_text: str) -> str:
        """Formats the return text for the Mermaid diagram.

        Adds double parentheses to the return text, unless it already contains parentheses.
        """
        if '(' in return_text:
            return f'(("return {return_text}"))'
        return f'((return {return_text}))'

    def _get_condition_text(self, test) -> str:
        """Extracts the condition text."""
        if isinstance(test, ast.Compare):
            left = self._get_name(test.left)
            op = self._get_operator(test.ops[0])
            right = self._get_name(test.comparators[0])
            return f'{left} {op} {right}'
        elif isinstance(test, ast.Name):
            return test.id
        elif isinstance(test, ast.Attribute):
            return f'{self._get_name(test.value)}.{test.attr}'
        return 'condition'

    def _get_call_text(self, call) -> str:
        """Extracts the function call text."""
        if isinstance(call.func, ast.Name):
            return f'{call.func.id}'
        elif isinstance(call.func, ast.Attribute):
            return f'{self._get_name(call.func.value)}.{call.func.attr}'
        return 'function_call'

    def _get_return_text(self, ret) -> str:
        """Extracts the return text."""
        if isinstance(ret.value, ast.Name):
            return ret.value.id
        elif isinstance(ret.value, ast.Call):
            return self._get_call_text(ret.value)
        return ''

    def _get_name(self, node) -> str:
        """Extracts the name of an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{self._get_name(node.value)}.{node.attr}'
        elif isinstance(node, ast.Call):
            node_args = ','.join([self._get_name(arg) for arg in node.args])
            return f'{self._get_name(node.func)}({node_args}).{node.args[0].id}'
        return str(node)

    def _get_operator(self, op) -> str:
        """Converts AST operator to string."""
        op_map = {
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.Lt: '<',
            ast.LtE: '<=',
            ast.Gt: '>',
            ast.GtE: '>=',
            ast.In: 'in',
            ast.NotIn: 'not in',
            ast.Is: 'is',
            ast.IsNot: 'is not',
        }
        return op_map.get(type(op), '?')

    def generate_admin_diagram(self, filename: str, app_name: str):
        """Generates Mermaid diagram for Admin classes."""
        tree = self.parse_file(filename)

        mermaid_code = ['```mermaid', 'flowchart TD']

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                bases += [
                    base.attr for base in node.bases if isinstance(base, ast.Attribute)
                ]
                if 'ModelAdmin' in bases:
                    class_id = f'admin_{node.name}'
                    mermaid_code.append(f'    {class_id}[{node.name}]')

                    # Adiciona configurações e métodos do admin
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            if isinstance(item.targets[0], ast.Name):
                                attr_name = item.targets[0].id
                                if attr_name in [
                                    'list_display',
                                    'search_fields',
                                    'list_filter',
                                ]:
                                    attr_id = f'{class_id}_{attr_name}'
                                    mermaid_code.append(
                                        f'    {class_id} --> {attr_id}[{attr_name}]'
                                    )
                        elif isinstance(item, ast.FunctionDef):
                            method_id = f'{class_id}_{item.name}'
                            mermaid_code.append(
                                f'    {class_id} --> {method_id}[{item.name}]'
                            )
                            # Analisa o corpo do método
                            node_counter = 0
                            for stmt in item.body:
                                node_counter = self._analyze_statement(
                                    stmt, method_id, mermaid_code, node_counter
                                )

        self.save_mermaid_diagram(
            mermaid_code, f"{app_name}_{filename.split('/')[-1].split('.')[0]}"
        )

    def generate_tasks_diagram(self, filename: str, app_name: str):
        """Generates Mermaid diagram for Celery tasks."""
        tree = self.parse_file(filename)

        mermaid_code = ['```mermaid', 'flowchart TD']
        node_counter = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Procura por decoradores @task
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if (
                            isinstance(decorator.func, ast.Name)
                            and decorator.func.id == 'task'
                        ):
                            task_id = f'task_{node.name}'
                            mermaid_code.append(f'    {task_id}[Task: {node.name}]')

                            # Adiciona docstring se existir
                            if docstring := ast.get_docstring(node):
                                doc_id = f'{task_id}_doc'
                                mermaid_code.append(
                                    f'    {task_id} --> {doc_id}["{docstring[:50]}..."]'
                                )

                            # Analisa o corpo da task
                            for stmt in node.body:
                                if not isinstance(stmt, ast.Expr):  # Pula a docstring
                                    node_counter = self._analyze_statement(
                                        stmt, task_id, mermaid_code, node_counter
                                    )

        self.save_mermaid_diagram(
            mermaid_code, f"{app_name}_{filename.split('/')[-1].split('.')[0]}"
        )
