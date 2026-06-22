# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""LaTeX helpers for parameter inventory document generation."""


def tex_escape(text):
    """Escape special LaTeX characters."""
    text = text.replace('\\', r'\textbackslash{}')
    for old, new in [
        ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
        ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
        ('~', r'\textasciitilde{}'), ('^', r'\^{}'),
    ]:
        text = text.replace(old, new)
    return text


def tt(text):
    """Wrap text in \\texttt with escaping."""
    return f'\\texttt{{{tex_escape(text)}}}'


def src(file_path, line=None):
    """Format a source file reference."""
    short = file_path.replace('src/models/', '')
    ref = f'{short}:{line}' if line else short
    return f'{{\\scriptsize {tt(ref)}}}'


def generate_document(sections):
    """Generate the full LaTeX parameter inventory document."""
    from datetime import datetime
    now = datetime.now()

    lines = [
        r'\documentclass[11pt,a4paper]{article}',
        r'\newcommand{\doctitle}{Model Parameter Inventory}',
        r'\newcommand{\docsubtitle}{Hard-Coded Input Parameters for Model Governance}',
        r'\newcommand{\docversion}{1.0}',
        f'\\newcommand{{\\docdate}}{{{now.strftime("%d-%B-%Y")}}}',
        r'\newcommand{\docauthor}{David K Kelly}',
        r'\input{../shared/mkm_header}',
        '',
        r'\begin{document}',
        r'\mkmtitlepage',
        r'\mkmlegalpage',
        r'\tableofcontents',
        r'\clearpage',
        '',
        # Executive summary
        r'\section{Executive Summary}',
        '',
        r'This document provides a complete inventory of all hard-coded input parameters used by the '
        r'MKM Physical Risk analytical models. It is maintained as part of the Model Risk Governance '
        r'framework and should be reviewed alongside each model\textquotesingle s documentation.',
        '',
        r'\subsection{Purpose}',
        r'Hard-coded parameters include physical constants, default function arguments, calibration '
        r'values, threshold tables, and factor look-ups. Documenting these centrally enables:',
        r'\begin{itemize}',
        r'    \item Audit trail for model validation and MRC review',
        r'    \item Impact assessment when parameters are recalibrated',
        r'    \item Identification of cross-model dependencies on shared constants',
        r'\end{itemize}',
        '',
        r'\subsection{Scope}',
        f'This inventory covers \\textbf{{{len(sections)}}} model modules containing the parameters '
        r'listed below. Each entry provides the parameter name, current value, description, and '
        r'source file with line number for traceability.',
        '',
        f'Generated on \\textbf{{{now.strftime("%d %B %Y")}}}.',
        r'\clearpage',
        '',
    ]

    # Generate each model section
    for section in sections:
        safe_title = tex_escape(section['title'])
        safe_id = tex_escape(section['model_id'])
        lines.append(f'\\section{{{safe_title} ({safe_id})}}')
        lines.append('')
        lines.append(f'Source: {tt(section["source"])}')
        lines.append('')

        for sub_title, params in section['subsections']:
            lines.append(f'\\subsection{{{tex_escape(sub_title)}}}')
            lines.append('')
            lines.append(r'\begin{longtable}{p{4cm}p{4cm}p{5.5cm}p{3.5cm}}')
            lines.append(r'    \toprule')
            lines.append(r'    \textbf{Parameter} & \textbf{Value} & \textbf{Description} & \textbf{Source} \\')
            lines.append(r'    \midrule')
            lines.append(r'    \endfirsthead')
            lines.append(r'    \toprule')
            lines.append(r'    \textbf{Parameter} & \textbf{Value} & \textbf{Description} & \textbf{Source} \\')
            lines.append(r'    \midrule')
            lines.append(r'    \endhead')
            lines.append(r'    \bottomrule')
            lines.append(r'    \endfoot')

            for name, value, desc, source_ref in params:
                lines.append(
                    f'    {tt(name)} & '
                    f'{tex_escape(value)} & '
                    f'{tex_escape(desc)} & '
                    f'{src(source_ref)} \\\\'
                )

            lines.append(r'\end{longtable}')
            lines.append('')

        lines.append(r'\clearpage')
        lines.append('')

    # Document history
    lines.append(r'\section{Document History}')
    lines.append(r'\begin{table}[ht]')
    lines.append(r'    \centering')
    lines.append(r'    \begin{tabular}{l|l|l|l}')
    lines.append(r'        \textbf{Date} & \textbf{Version} & \textbf{Description} & \textbf{Author} \\')
    lines.append(r'        \hline')
    lines.append(f'        {now.strftime("%d-%b-%Y")} & 1.0 & Initial parameter inventory & D. Kelly \\\\')
    lines.append(r'    \end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    lines.append(r'\end{document}')

    return '\n'.join(lines)
