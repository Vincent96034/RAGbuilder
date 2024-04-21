from typing import Union
from pathlib import Path


def from_file(
    template_file: Union[str, Path],
) -> str:
    """Load a prompt from a file.

    Args:
        template_file: The path to the file containing the prompt template.
        input_variables: [DEPRECATED] A list of variable names the final prompt
            template will expect.

    input_variables is ignored as from_file now delegates to from_template().

    Returns:
        The prompt loaded from the file.
    """
    with open(str(template_file), "r") as f:
        template = f.read()
    return template
