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

"""Static LaTeX body — purpose, authority, membership, responsibilities."""

BODY_GOVERNANCE = r"""}
\newcommand{\docauthor}{David K Kelly, Johnny Mattimore}

\input{../shared/mkm_header}

\begin{document}
\mkmtitlepage
\mkmlegalpage
\tableofcontents
\clearpage

% ================================================================
\section{Introduction}
% ================================================================

This document defines the Terms of Reference (ToR) for the Model Risk Committee
(MRC) of MKM Research Labs. The MRC is the principal governance body
responsible for overseeing the model risk management framework as described in
the \textit{Handbook of Model Risk Management for Vendors} (Kelly, Mattimore 2025).

The Terms of Reference establish the committee's authority, responsibilities,
membership, and operating procedures. They are reviewed annually and updated as
required to reflect changes in the regulatory environment, organisational
structure, or model landscape.

% ================================================================
\section{Purpose and Mandate}
% ================================================================

The Model Risk Committee is established to:

\begin{enumerate}[label=\arabic*.]
    \item Provide independent oversight of all models used across the platform,
          from development through to retirement.
    \item Ensure that model risk is identified, assessed, monitored, and
          mitigated in accordance with the governance framework.
    \item Approve the deployment of new models and material changes to existing
          models into production.
    \item Set and enforce model risk appetite, tiering standards, and validation
          requirements.
    \item Review model performance, limitations, and remediation actions on a
          regular cycle.
    \item Ensure compliance with regulatory expectations, including SS1/23 (PRA),
          SR~11-7 (Federal Reserve), and the EBA Guidelines on model risk
          management.
\end{enumerate}

% ================================================================
\section{Authority}
% ================================================================

The MRC derives its authority from the Board of Directors and the Chief Risk
Officer. The committee has the authority to:

\begin{itemize}
    \item Approve or reject models for production deployment.
    \item Impose conditions, limitations, or restrictions on model usage.
    \item Require remediation actions and set deadlines for completion.
    \item Escalate material model risk issues to the Board or relevant
          regulatory bodies.
    \item Commission independent model validation reviews.
    \item Approve changes to model risk policies, standards, and procedures.
    \item Request any information, documentation, or analysis from model owners
          and development teams.
\end{itemize}

% ================================================================
\section{Membership}
% ================================================================

\subsection{Standing Members}

\begin{longtable}{p{4cm}p{5cm}p{4cm}}
\toprule
\textbf{Name} & \textbf{Role} & \textbf{Committee Role} \\
\midrule
\endhead
Johnny Mattimore & Managing Director & Chair \\
David K Kelly & Chief Science Officer & Model Owner \\
\bottomrule
\end{longtable}

\subsection{Quorum}

A quorum shall consist of the Chair (or Deputy Chair) and at least one
additional standing member. Decisions require a simple majority of those
present. Where the committee is split, the Chair holds the casting vote.

\subsection{Attendees and Invitees}

The following may attend MRC meetings by invitation:

\begin{itemize}
    \item Model developers and quantitative analysts (for model presentations)
    \item Independent validators (internal or external)
    \item Internal audit representatives
    \item External regulators or auditors (as observers)
    \item Technology and infrastructure leads (for implementation matters)
\end{itemize}

% ================================================================
\section{Responsibilities}
% ================================================================

\subsection{Model Lifecycle Oversight}

The MRC is responsible for governance at each stage of the model lifecycle:

\begin{longtable}{p{3.5cm}p{10cm}}
\toprule
\textbf{Stage} & \textbf{MRC Responsibility} \\
\midrule
\endhead
Development & Review model design, methodology selection, and development
              standards. Approve progression to validation. \\[6pt]
Validation & Commission independent validation. Review validation findings
             and determine whether conditions are required for approval. \\[6pt]
Production & Grant production approval (with or without conditions). Monitor
             ongoing performance and trigger periodic reviews. \\[6pt]
Retirement & Approve model decommissioning. Ensure replacement models are
             validated before transition. \\
\bottomrule
\end{longtable}

\subsection{Model Risk Assessment}

\begin{itemize}
    \item Maintain the model inventory, ensuring all models are registered,
          tiered, and assigned owners.
    \item Apply the tiering matrix (Materiality $\times$ Complexity) as defined
          in Chapter~8 of the Handbook to determine governance intensity.
    \item Assign and review RAG ratings for each model.
    \item Monitor remediation actions and track open items to closure.
\end{itemize}

\subsection{Validation Standards}

\begin{itemize}
    \item Define validation scope and depth requirements by model tier.
    \item Review and approve validation reports.
    \item Ensure validators are independent from model development.
    \item Set standards for backtesting, benchmarking, and sensitivity analysis.
\end{itemize}

\subsection{Documentation Standards}

The MRC shall ensure that all models maintain documentation to the standard
required by the Handbook, including:

\begin{itemize}
    \item Model purpose and scope
    \item Mathematical framework and methodology
    \item Input parameters and calibration (per the Parameter Inventory)
    \item Implementation details and source code references
    \item Sensitivity analysis results
    \item Validation and backtesting results
    \item Known limitations and assumptions
    \item Change history and version control
\end{itemize}

"""
