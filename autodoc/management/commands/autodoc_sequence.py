import ast
import os
from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Gera documentação automática em formato MermaidJS para views, admins e tasks Celery de apps Django"

    def add_arguments(self, parser):
        parser.add_argument('app_names', nargs='+', type=str, help='Nome dos apps Django para documentar')

    def handle(self, *args, **options):
        for app_name in options['app_names']:
            if app_name not in settings.INSTALLED_APPS:
                raise CommandError(f'App "{app_name}" não está em INSTALLED_APPS')

            self.process_app(app_name)

    def process_app(self, app_name: str):
        """Processa um app Django e gera documentação para seus componentes."""
        app_path = self.get_app_path(app_name)

        # Arquivos a serem analisados
        views_file = os.path.join(app_path, 'views.py')
        admin_file = os.path.join(app_path, 'admin.py')
        tasks_file = os.path.join(app_path, 'tasks.py')

        # Gera documentação se os arquivos existirem
        if os.path.exists(views_file):
            self.generate_views_diagram(views_file, app_name)

        if os.path.exists(admin_file):
            self.generate_admin_diagram(admin_file, app_name)

        if os.path.exists(tasks_file):
            self.generate_tasks_diagram(tasks_file, app_name)

    def get_app_path(self, app_name: str) -> str:
        """Retorna o caminho do app Django."""
        module = __import__(app_name)
        return os.path.dirname(module.__file__)

    def parse_file(self, filename: str) -> ast.AST:
        """Faz o parse de um arquivo Python."""
        with open(filename, 'r') as f:
            return ast.parse(f.read())

    def generate_views_diagram(self, filename: str, app_name: str):
        """Gera diagrama de sequência Mermaid para views."""
        tree = self.parse_file(filename)

        mermaid_code = ["sequenceDiagram"]

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Identifica views baseadas em classes
                bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                if any(base.endswith('View') for base in bases):
                    view_name = node.name

                    # Adiciona participantes
                    mermaid_code.append(f"    participant Client")
                    mermaid_code.append(f"    participant {view_name}")

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name in ['get', 'post', 'put', 'delete']:
                                # Adiciona a chamada do método
                                mermaid_code.append(f"    Client->>+{view_name}: {item.name}()")

                                # Analisa o corpo do método
                                self._analyze_sequence_body(item.body, view_name, mermaid_code)

                                # Fecha a chamada do método
                                mermaid_code.append(f"    {view_name}-->>-Client: response")

        self.save_mermaid_diagram(mermaid_code, f"{app_name}_views")

    def _analyze_sequence_body(self, body, participant: str, mermaid_code: List[str], depth: int = 0):
        """Analisa o corpo de um método para o diagrama de sequência."""
        for stmt in body:
            if isinstance(stmt, ast.If):
                condition = self._get_condition_text(stmt.test)
                mermaid_code.append(f"    Note over {participant}: if {condition}")
                self._analyze_sequence_body(stmt.body, participant, mermaid_code, depth + 1)

                if stmt.orelse:
                    mermaid_code.append(f"    Note over {participant}: else")
                    self._analyze_sequence_body(stmt.orelse, participant, mermaid_code, depth + 1)

            elif isinstance(stmt, ast.Call):
                target = self._get_call_target(stmt)
                if target != participant:  # Evita mostrar chamadas internas
                    mermaid_code.append(f"    {participant}->>+{target}: {self._get_call_text(stmt)}")
                    mermaid_code.append(f"    {target}-->>-{participant}: response")

            elif isinstance(stmt, ast.Return):
                return_text = self._get_return_text(stmt)
                if return_text:
                    mermaid_code.append(f"    Note over {participant}: return {return_text}")

    def _get_call_target(self, call) -> str:
        """Extrai o alvo da chamada de função."""
        if isinstance(call.func, ast.Name):
            return call.func.id
        elif isinstance(call.func, ast.Attribute):
            if isinstance(call.func.value, ast.Name):
                return call.func.value.id
            elif isinstance(call.func.value, ast.Call):
                return self._get_call_target(call.func.value)
        return "External"

    def _get_condition_text(self, test) -> str:
        """Extrai o texto da condição."""
        if isinstance(test, ast.Compare):
            left = self._get_name(test.left)
            op = self._get_operator(test.ops[0])
            right = self._get_name(test.comparators[0])
            return f"{left} {op} {right}"
        elif isinstance(test, ast.Name):
            return test.id
        return "condition"

    def _get_call_text(self, call) -> str:
        """Extrai o texto da chamada de função."""
        if isinstance(call.func, ast.Name):
            return f"{call.func.id}()"
        elif isinstance(call.func, ast.Attribute):
            return f"{self._get_name(call.func.value)}.{call.func.attr}()"
        return "function_call"

    def _get_return_text(self, ret) -> str:
        """Extrai o texto do return."""
        if isinstance(ret.value, ast.Name):
            return ret.value.id
        elif isinstance(ret.value, ast.Call):
            return self._get_call_text(ret.value)
        return ""

    def generate_admin_diagram(self, filename: str, app_name: str):
        """Gera diagrama de sequência Mermaid para classes Admin."""
        tree = self.parse_file(filename)

        mermaid_code = ["sequenceDiagram"]

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                if 'ModelAdmin' in bases:
                    admin_name = node.name

                    # Adiciona participantes
                    mermaid_code.append(f"    participant User")
                    mermaid_code.append(f"    participant {admin_name}")
                    mermaid_code.append(f"    participant Database")

                    # Adiciona configurações do admin como notas
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            if isinstance(item.targets[0], ast.Name):
                                attr_name = item.targets[0].id
                                if attr_name in ['list_display', 'search_fields', 'list_filter']:
                                    mermaid_code.append(f"    Note over {admin_name}: {attr_name}")

                        elif isinstance(item, ast.FunctionDef):
                            # Adiciona a chamada do método
                            mermaid_code.append(f"    User->>+{admin_name}: {item.name}()")

                            # Analisa o corpo do método
                            self._analyze_sequence_body(item.body, admin_name, mermaid_code)

                            # Simula interação com banco de dados
                            mermaid_code.append(f"    {admin_name}->>+Database: query")
                            mermaid_code.append(f"    Database-->>-{admin_name}: data")

                            # Fecha a chamada do método
                            mermaid_code.append(f"    {admin_name}-->>-User: response")

        self.save_mermaid_diagram(mermaid_code, f"{app_name}_admin")

    def generate_tasks_diagram(self, filename: str, app_name: str):
        """Gera diagrama de sequência Mermaid para tasks Celery."""
        tree = self.parse_file(filename)

        mermaid_code = ["sequenceDiagram"]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Procura por decoradores @task
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == 'task':
                            task_name = node.name

                            # Adiciona participantes
                            mermaid_code.append(f"    participant App")
                            mermaid_code.append(f"    participant Celery")
                            mermaid_code.append(f"    participant {task_name}")

                            # Adiciona docstring como nota se existir
                            if docstring := ast.get_docstring(node):
                                mermaid_code.append(f"    Note over {task_name}: {docstring[:50]}...")

                            # Simula o fluxo da task
                            mermaid_code.append(f"    App->>+Celery: {task_name}.delay()")
                            mermaid_code.append(f"    Celery->>+{task_name}: execute")

                            # Analisa o corpo da task
                            for stmt in node.body:
                                if not isinstance(stmt, ast.Expr):  # Pula a docstring
                                    self._analyze_sequence_body([stmt], task_name, mermaid_code)

                            # Fecha o fluxo da task
                            mermaid_code.append(f"    {task_name}-->>-Celery: result")
                            mermaid_code.append("    Celery-->>-App: task_id")

        self.save_mermaid_diagram(mermaid_code, f"{app_name}_tasks")

    def save_mermaid_diagram(self, mermaid_code: List[str], filename: str):
        """Salva o diagrama Mermaid em um arquivo."""
        output_dir = 'docs/mermaid/sequence'
        os.makedirs(output_dir, exist_ok=True)

        with open(f"{output_dir}/{filename}.mmd", 'w') as f:
            f.write('\n'.join(mermaid_code))

        self.stdout.write(self.style.SUCCESS(f'Diagrama Mermaid gerado com sucesso: {filename}.mmd'))
