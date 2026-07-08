from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt

PAGE_WIDTH_CHARS = 100
LINES_PER_PAGE = 46


def _wrap_paragraph(text: str) -> list[str]:
    if not text.strip():
        return [""]
    return textwrap.wrap(text, width=PAGE_WIDTH_CHARS) or [""]


def markdown_to_lines(markdown_text: str) -> list[str]:
    """Converte markdown simples (titulos #, tabelas, listas, paragrafos)
    em uma lista de linhas de texto monoespacado prontas para paginacao.
    Suficiente para relatorios/slides deste projeto - nao e um renderer de
    markdown completo."""
    lines: list[str] = []
    for raw_line in markdown_text.split("\n"):
        line = raw_line.rstrip()
        if line.startswith("# "):
            lines.append(line[2:].upper())
            lines.append("=" * min(len(line[2:]), PAGE_WIDTH_CHARS))
        elif line.startswith("## "):
            lines.append("")
            lines.append(line[3:])
            lines.append("-" * min(len(line[3:]), PAGE_WIDTH_CHARS))
        elif line.startswith("### "):
            lines.append("")
            lines.append(line[4:])
        elif line.startswith("|"):
            lines.append(line)
        elif line.startswith("- ") or line.startswith("* "):
            lines.extend(_wrap_paragraph_indented(line[2:], "  - "))
        elif re.match(r"^\d+\. ", line):
            lines.extend(_wrap_paragraph_indented(re.sub(r"^\d+\. ", "", line), "  " + line.split(".")[0] + ". "))
        elif line.strip() == "":
            lines.append("")
        else:
            lines.extend(_wrap_paragraph(line))
    return lines


def _wrap_paragraph_indented(text: str, prefix: str) -> list[str]:
    wrapped = textwrap.wrap(text, width=PAGE_WIDTH_CHARS - len(prefix)) or [""]
    result = [prefix + wrapped[0]]
    for extra in wrapped[1:]:
        result.append(" " * len(prefix) + extra)
    return result


def render_markdown_pdf(markdown_path: str | Path, output_path: str | Path) -> int:
    """Le um arquivo markdown, pagina o conteudo e escreve um PDF real via
    matplotlib. Retorna o numero de paginas geradas."""
    text = Path(markdown_path).read_text()
    lines = markdown_to_lines(text)

    pages = [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[""]]

    with PdfPages(output_path) as pdf:
        for page_lines in pages:
            fig = plt.figure(figsize=(8.27, 11.69))  # A4
            fig.text(
                0.08,
                0.95,
                "\n".join(page_lines),
                family="monospace",
                fontsize=8,
                verticalalignment="top",
            )
            pdf.savefig(fig)
            plt.close(fig)

    return len(pages)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: render_report_pdf.py MARKDOWN_PATH OUTPUT_PDF_PATH", file=sys.stderr)
        raise SystemExit(2)
    n_pages = render_markdown_pdf(sys.argv[1], sys.argv[2])
    print(f"wrote {sys.argv[2]}: {n_pages} pages")
