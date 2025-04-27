from jinja2 import Environment, FileSystemLoader

# Configuration de Jinja2
env = Environment(loader=FileSystemLoader("abrege_service/prompts/templates"))


def generate_prompt(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(context)
