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

"""Static LaTeX body — meetings, tiering, escalation, review (tail)."""

BODY_OPERATIONS = r"""% ================================================================
\section{Meeting Frequency and Procedures}
% ================================================================

\subsection{Meeting Schedule}

\begin{longtable}{p{4cm}p{9.5cm}}
\toprule
\textbf{Meeting Type} & \textbf{Frequency and Purpose} \\
\midrule
\endhead
Regular Meeting & Quarterly. Full review of model inventory, risk dashboard,
                  remediation tracker, and upcoming reviews. \\[6pt]
Approval Meeting & As required. Convened to approve new models or material
                   changes for production deployment. \\[6pt]
Extraordinary Meeting & As required. Convened for urgent matters such as model
                        failures, material findings, or regulatory requests. \\[6pt]
Annual Review & Annual. Comprehensive review of the model risk framework,
                policies, tiering matrix, and these Terms of Reference. \\
\bottomrule
\end{longtable}

\subsection{Agenda and Papers}

\begin{itemize}
    \item The agenda shall be circulated at least 5 business days before each
          meeting.
    \item Supporting papers (model documentation, validation reports, risk
          dashboards) shall be circulated at least 3 business days before.
    \item The Model Risk Dashboard (as implemented in the governance platform)
          shall be presented at each regular meeting.
\end{itemize}

\subsection{Minutes and Records}

\begin{itemize}
    \item Minutes shall be recorded for all meetings and approved at the
          following meeting.
    \item Decisions, action items, and conditions shall be logged in the
          governance audit trail.
    \item All MRC decisions are recorded with full audit trail (timestamp, user,
          rationale) in the platform's governance module.
\end{itemize}

% ================================================================
\section{Model Tiering Framework}
% ================================================================

The MRC applies the tiering matrix from Chapter~8 (Proportionality) of the
Handbook. Governance intensity is proportional to model tier:

\begin{longtable}{p{2cm}p{3cm}p{8.5cm}}
\toprule
\textbf{Tier} & \textbf{Risk Level} & \textbf{Governance Requirements} \\
\midrule
\endhead
Tier~1 & Maximum & Full independent validation, quarterly MRC review,
         annual recertification, mandatory benchmarking. \\[6pt]
Tier~2 & Substantial & Independent validation, semi-annual MRC review,
         annual recertification. \\[6pt]
Tier~3 & Moderate & Peer review, annual MRC review, biennial
         recertification. \\[6pt]
Tier~4 & Minimal & Self-assessment, annual MRC notification, triennial
         recertification. \\
\bottomrule
\end{longtable}

\noindent The current model inventory contains models tiered as follows:

\begin{center}
\begin{tabular}{lcccc}
\toprule
& \textbf{Tier 1} & \textbf{Tier 2} & \textbf{Tier 3} & \textbf{Tier 4} \\
\midrule
Count & 2 & 3 & 3 & 0 \\
\bottomrule
\end{tabular}
\end{center}

% ================================================================
\section{Escalation and Reporting}
% ================================================================

\subsection{Escalation Triggers}

The following events require immediate escalation to the Chair:

\begin{itemize}
    \item A Tier~1 or Tier~2 model fails validation or backtesting.
    \item A model produces outputs that materially differ from expectations
          or benchmarks.
    \item A regulatory inquiry or finding relates to model risk.
    \item A material limitation or assumption is found to be violated.
    \item A remediation action exceeds its deadline by more than 30 days.
\end{itemize}

\subsection{Board Reporting}

The MRC Chair shall provide a quarterly summary to the Board covering:

\begin{itemize}
    \item Overall model risk posture (aggregate RAG distribution).
    \item Key model approvals, rejections, and conditional approvals.
    \item Open remediation items and overdue reviews.
    \item Regulatory developments affecting model governance.
\end{itemize}

% ================================================================
\section{Review of Terms of Reference}
% ================================================================

These Terms of Reference shall be reviewed annually by the MRC and approved
by the Board. Material changes to the ToR require Board approval. Minor
administrative updates may be approved by the MRC Chair.

\vspace{1em}
\noindent\textbf{Next scheduled review:} """
