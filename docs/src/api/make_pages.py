"""Generate the api pages and navigation.
NOTE: Works best when following the Google style guide
https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
"""

import mkdocs_gen_files
from pathlib import Path
import os
import subprocess

package = os.getenv("PACKAGE")

element = package.split("_", 1)[1]
if not Path(f"workflow_{element}").is_dir():
    try:
        subprocess.run(
            f"git clone https://github.com/tdincer/workflow-{element.replace('_','-')}.git /main/delete".split(
                " "
            ),
            check=True,
            timeout=5,
        )
        os.system(f"mv /main/delete/workflow_{element} /main/")
        os.system("rm -fR /main/delete")
    except subprocess.CalledProcessError:
        pass  # no repo found

nav = mkdocs_gen_files.Nav()
for path in sorted(Path(package).glob("**/*.py")) + sorted(
    Path(f"workflow_{element}").glob("**/*.py")
):
    if path.stem == "__init__":
        continue
    with mkdocs_gen_files.open(f"api/{path.with_suffix('')}.md", "w") as f:
        module_path = ".".join(
            [p for p in path.with_suffix("").parts if p != "__init__"]
        )
        print(f"::: {module_path}", file=f)
    nav[path.parts] = f"{path.with_suffix('')}.md"

with mkdocs_gen_files.open("api/navigation.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
