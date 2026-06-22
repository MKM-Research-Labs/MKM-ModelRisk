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

"""Test history tracking — records test suite changes across runs."""

import json
import os

from .latex import tex_escape

_history_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'test_history.json'))


def _load_history():
    """Load test run history from JSON file."""
    try:
        with open(_history_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_history(history):
    """Save test run history to JSON file."""
    with open(_history_path, 'w') as f:
        json.dump(history, f, indent=2)


def update_history(by_model, run_timestamp):
    """Update history, adding an entry when test count changes for a model.

    Returns the full history dict (model_id -> list of entries).
    """
    history = _load_history()
    date_str = run_timestamp.strftime('%d-%b-%Y')

    for model_id, results in by_model.items():
        test_names = sorted(r['nodeid'] for r in results)
        n_total = len(results)
        n_pass = sum(1 for r in results if r['outcome'] == 'passed')
        n_fail = sum(1 for r in results if r['outcome'] == 'failed')

        model_history = history.get(model_id, [])
        prev_names = set(model_history[-1]['test_names']) if model_history else set()
        curr_names = set(test_names)

        added = curr_names - prev_names
        removed = prev_names - curr_names

        if not model_history:
            desc = f'Initial test suite ({n_total} tests)'
            model_history.append({
                'date': date_str,
                'version': '1.0',
                'description': desc,
                'author': 'D. Kelly',
                'total': n_total,
                'passed': n_pass,
                'failed': n_fail,
                'test_names': test_names,
            })
        elif added or removed:
            prev_ver = model_history[-1].get('version', '1.0')
            parts = prev_ver.split('.')
            new_ver = f'{parts[0]}.{int(parts[1]) + 1}'

            desc_parts = []
            if added:
                desc_parts.append(f'{len(added)} test(s) added')
            if removed:
                desc_parts.append(f'{len(removed)} test(s) removed')
            desc = '; '.join(desc_parts) + f' (total: {n_total})'

            model_history.append({
                'date': date_str,
                'version': new_ver,
                'description': desc,
                'author': 'D. Kelly',
                'total': n_total,
                'passed': n_pass,
                'failed': n_fail,
                'test_names': test_names,
            })
        else:
            model_history[-1]['date'] = date_str
            model_history[-1]['passed'] = n_pass
            model_history[-1]['failed'] = n_fail

        history[model_id] = model_history

    _save_history(history)
    return history


def generate_history_table(model_id, history):
    """Generate a LaTeX history table matching the \\mkmhistorypage format."""
    model_history = history.get(model_id, [])
    if not model_history:
        return ''

    lines = [
        r'\subsection{Test Document History}',
        r'\begin{table}[ht]',
        r'    \centering',
        r'    \begin{tabular}{l|l|l|l}',
        r'        \textbf{Date} & \textbf{Version} & \textbf{Description} & \textbf{Author} \\',
        r'        \hline',
    ]

    for entry in model_history:
        lines.append(
            f'        {tex_escape(entry["date"])} & '
            f'{tex_escape(entry["version"])} & '
            f'{tex_escape(entry["description"])} & '
            f'{tex_escape(entry["author"])} \\\\'
        )

    lines += [
        r'    \end{tabular}',
        r'\end{table}',
    ]
    return '\n'.join(lines)
