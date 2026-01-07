"""At the root of the project directory run
`> uv run examples/summarize_project_opencode.py`
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

from agf.agent import AgentRunner

result = AgentRunner.run(
    "opencode",
    """
    Generate a quick summary of this project

    ## Output Format

    IMPORTANT: Return a JSON with this structure:

    ```json
    {
      "summary": "short summary of the project",
      "core_components": [
        {
          "name": "name of the component",
          "description": "description of the component"
        }
      ]
    }
    ```
    """,
)

print(f"duration_seconds: {result.duration_seconds}")
print(f"exit_code: {result.exit_code}")
print(f"error: {result.error}")
print(f"output: {result.output}")
print(f"parsed_output: {result.parsed_output}")
print(f"agent_name: {result.agent_name}")
