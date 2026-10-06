from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Configuration de Jinja2
env = Environment(loader=FileSystemLoader("abrege_service/prompts/templates"))


def generate_prompt(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(context)


SUMMARY_TEMPLATES_DIR = Path(__file__).parent / "templates" / "summary"


def load_summary_template(name: str) -> str:
    """Read a raw LangChain prompt template (`{variable}` syntax) from templates/summary/<name>.txt."""
    return (SUMMARY_TEMPLATES_DIR / f"{name}.txt").read_text(encoding="utf-8")
