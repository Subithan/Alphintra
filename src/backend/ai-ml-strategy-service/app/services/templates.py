from typing import Dict


def project_template(template: str) -> Dict[str, str]:
    template = (template or "trading").lower()
    if template == "trading":
        return {
            "main.py": (
                "# AI-powered trading strategy\n"
                "# Implement your logic in TradingStrategy.execute\n\n"
                "import pandas as pd\n"
                "from typing import Dict\n\n"
                "class TradingStrategy:\n"
                "    def __init__(self):\n"
                "        self.name = \"AI Generated Strategy\"\n\n"
                "    def execute(self, data: pd.DataFrame) -> Dict:\n"
                "        # TODO: Implement signals and risk management\n"
                "        return {\"signals\": []}\n"
            )
        }
    elif template == "ml":
        return {
            "model.py": (
                "# ML research scaffold\n\n"
                "import numpy as np\n"
                "from sklearn.linear_model import LinearRegression\n"
                "\nmodel = LinearRegression()\n"
            )
        }
    else:
        return {"README.md": "# New Project\n\nStart building with Alphintra IDE.\n"}
