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
PAGE_BREAK = "\x0c"


def _strip_emphasis(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    return text


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
        line = _strip_emphasis(raw_line.rstrip())
        if line.startswith("# "):
            # Cada titulo de nivel 1 comeca uma pagina nova - documentos com
            # um unico "# Titulo" (como o relatorio tecnico) fluem
            # continuamente como antes; documentos com varios "# Slide N"
            # (como o deck do pitch) ganham uma pagina por slide.
            if lines:
                lines.append(PAGE_BREAK)
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
            if len(line) <= PAGE_WIDTH_CHARS:
                lines.append(line)
            else:
                # Nunca truncar: uma linha de tabela mais larga que a
                # pagina e quebrada (perde o alinhamento de colunas, mas
                # preserva todo o conteudo - preservar informacao importa
                # mais do que a tabela ficar bonita).
                lines.extend(textwrap.wrap(line, width=PAGE_WIDTH_CHARS, break_long_words=False) or [line])
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


def _chunk_into_pages(lines: list[str]) -> list[list[str]]:
    return [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[""]]


def render_markdown_pdf(markdown_path: str | Path, output_path: str | Path) -> int:
    """Le um arquivo markdown, pagina o conteudo e escreve um PDF real via
    matplotlib. Retorna o numero de paginas geradas."""
    text = Path(markdown_path).read_text()
    lines = markdown_to_lines(text)

    pages: list[list[str]] = []
    current_block: list[str] = []
    for line in lines:
        if line == PAGE_BREAK:
            if current_block:
                pages.extend(_chunk_into_pages(current_block))
            current_block = []
        else:
            current_block.append(line)
    if current_block:
        pages.extend(_chunk_into_pages(current_block))
    if not pages:
        pages = [[""]]

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
