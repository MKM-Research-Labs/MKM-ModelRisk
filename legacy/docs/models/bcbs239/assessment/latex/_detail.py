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

"""Per-principle detail sections, remediation roadmap and appendix."""

from .escape import tex_escape
from ..data import score_label, score_color


def build_principle_sections(principles, categories):
    """One \\section per category, with a \\subsection per principle."""
    doc = ''
    for cat_name, cat_ids in categories:
        doc += '\n% ================================================================\n'
        doc += f'\\section{{{tex_escape(cat_name)}}}\n'
        doc += '% ================================================================\n\n'

        cat_principles = [p for p in principles if p['id'] in cat_ids]
        for p in cat_principles:
            pid = p['id']
            title = tex_escape(p['title'])
            sc = p['score']
            status = tex_escape(score_label(sc))

            doc += f'\\subsection{{Principle {pid}: {title}}}\n\n'

            # Score box
            doc += r'\begin{table}[H]' + '\n'
            doc += r'    \centering' + '\n'
            doc += r'    \begin{tabular}{ll}' + '\n'
            doc += r'        \toprule' + '\n'
            doc += f'        Score & {score_color(sc)}{{\\textbf{{{sc}/4 --- {status}}}}} \\\\\n'
            if p.get('target_date'):
                doc += f"        Target Date & {tex_escape(p['target_date'])} \\\\\n"
            doc += r'        \bottomrule' + '\n'
            doc += r'    \end{tabular}' + '\n'
            doc += r'\end{table}' + '\n\n'

            # Description
            doc += r'\paragraph{Principle Description}' + '\n'
            doc += tex_escape(p.get('description', '')) + '\n\n'

            # Evidence
            if p.get('evidence'):
                doc += r'\paragraph{Evidence of Compliance}' + '\n'
                doc += tex_escape(p['evidence']) + '\n\n'

            # Gaps
            if p.get('gaps'):
                doc += r'\paragraph{Identified Gaps}' + '\n'
                doc += tex_escape(p['gaps']) + '\n\n'

            # Remediation
            if p.get('remediation'):
                doc += r'\paragraph{Remediation Plan}' + '\n'
                doc += tex_escape(p['remediation'])
                if p.get('target_date'):
                    doc += f" (Target: {tex_escape(p['target_date'])})"
                doc += '\n\n'

        doc += r'\clearpage' + '\n'
    return doc


def build_roadmap_and_appendix(principles, data, today):
    """Remediation roadmap table, appendix of principles, and history page."""
    doc = r"""
% ================================================================
\section{Remediation Roadmap}
% ================================================================

The following table summarises all identified gaps and their remediation plans,
ordered by target date.

\begin{longtable}{p{0.5cm}p{3cm}p{5.5cm}p{2.5cm}p{1.5cm}p{2cm}}
    \toprule
    \textbf{\#} & \textbf{Principle} & \textbf{Remediation Action} & \textbf{Gap Summary} & \textbf{Score} & \textbf{Target} \\
    \midrule
    \endhead
"""

    # Sort by target date
    sorted_principles = sorted(principles, key=lambda p: p.get('target_date', '9999'))
    for p in sorted_principles:
        if p.get('remediation'):
            sc = p['score']
            doc += (
                f"    {p['id']} & {tex_escape(p['title'])} & "
                f"{tex_escape(p['remediation'])} & "
                f"{tex_escape((p.get('gaps') or '')[:80])} & "
                f"{score_color(sc)}{{{sc}/4}} & "
                f"{tex_escape(p.get('target_date', ''))} \\\\\n"
            )

    doc += r"""    \bottomrule
\end{longtable}

\clearpage

% ================================================================
\section{Appendix: BCBS 239 Principles}
% ================================================================

For reference, the complete list of the 14 principles as defined by the Basel
Committee on Banking Supervision in January 2013 (\textit{Principles for
effective risk data aggregation and risk reporting}, BCBS 2013).

\begin{longtable}{cp{3cm}p{10.5cm}}
    \toprule
    \textbf{\#} & \textbf{Principle} & \textbf{Description} \\
    \midrule
    \endhead
"""

    for p in principles:
        doc += f"    {p['id']} & {tex_escape(p['title'])} & {tex_escape(p.get('description', ''))} \\\\\n"
        doc += '    \\addlinespace\n'

    doc += r"""    \bottomrule
\end{longtable}

% ================================================================
\mkmhistorypage{
""" + today + r""" & 1.0 & Initial BCBS 239 Self-Assessment & """ + tex_escape(data.get('assessor', 'David K Kelly')) + r""" \\
}

\end{document}
"""
    return doc
