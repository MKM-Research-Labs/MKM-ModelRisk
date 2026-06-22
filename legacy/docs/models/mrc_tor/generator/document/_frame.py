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

"""Static LaTeX preamble and closing frame for the MRC ToR document."""

HEADER = r"""\documentclass[11pt]{article}

\newcommand{\doctitle}{Model Risk Committee}
\newcommand{\docsubtitle}{Terms of Reference}
\newcommand{\docversion}{1.0}
\newcommand{\docdate}{"""

FOOTER = r"""

% ================================================================
\section{Approval}
% ================================================================

\vspace{1cm}
\begin{longtable}{p{6cm}p{7.5cm}}
\textbf{Approved by:} & \\[1.5cm]
\dotfill & \dotfill \\
Johnny Mattimore & David K Kelly \\
Chair, Model Risk Committee & Model Owner, Chief Science Officer \\[1cm]
\textbf{Date:} & \docdate \\
\end{longtable}

% ================================================================
\mkmhistorypage{
\docdate & 1.0 & Initial Terms of Reference & David K Kelly \\
}

\end{document}
"""
